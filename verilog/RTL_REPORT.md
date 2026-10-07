# radio_digital RTL report (2026-10-07)

## Files
| File | Content |
|---|---|
| `verilog/rtl/radio_digital.v` | Top: reset/strap latch, synchronisers, 130-clock sample divider, sc_phi1/2, code debounce, raw modes, 7-seg, uio |
| `verilog/rtl/rd_gold.v` | Shared LFSR pair (RX template / TX chips) + LFSR2 start-state precompute on code change |
| `verilog/rtl/rd_corr.v` | 4-phase chip slicer (8-sample majority), 4 x 127-bit chip registers, one shared sequential popcount |
| `verilog/rtl/rd_rx.v` | Trim servo, events (threshold 97, dedup 8), 2-of-3 pairing, holdoff, LED |
| `verilog/rtl/rd_tx.v` | 3 x (127 + 64) chip send FSM |
| `verilog/test/Makefile`, `test_radio.py` | cocotb tests (icarus by default) |
| `verilog/test/icarus_bin/{vvp,iverilog}` | Wrappers: oss-cad-suite's `bin/vvp` runs with its bundled glibc and cannot load the system libpython; the wrapper runs `libexec/vvp` with the system libraries. The Makefile uses it automatically |
| `openlane/radio_digital/pin_order.cfg` | N: clk, rst_n, ui_in, uio_*, uo_out. S: trim_out, comp_in, sc_phi1/2, rx_en, tx_en |
| `verilog/test/vectors/README.md` | One-line fix: the LFSR "output = MSB" wording was wrong. In the `lfsr2` integers, stage 1 is bit 6 and the output (stage 7) is bit 0 |

`openlane/radio_digital/config.tcl` still names `r2r_dac_control` and its files. Update DESIGN_NAME/VERILOG_FILES before hardening. I didn't edit it because it was outside my scope.

## Ports
`clk, rst_n, ui_in[7:0], uio_in[7:0], uo_out[7:0], uio_out[7:0], uio_oe[7:0], comp_in, trim_out[7:0], tx_en, rx_en, sc_phi1, sc_phi2`. These are as suggested.
- `ui_in[6:0]` is the code: 2-flop synchronised, then debounced (adopted after it has been stable and different for 48 chips = 50 ms, and not during a TX send). `ui_in[7]` is the role, latched at reset.
- **Mode strap:** at reset release, `mode = uio_in[1:0]` only if `uio_in[7:4] == 4'b1010`, else code mode. The modes are 00 code, 01 raw TX, 10 data (reserved, behaves as code), 11 reserved (code). `uio_oe` is 0 during reset and becomes 8'b11111000 one clock after release. The RP2350 must therefore stop driving uio[7:4] right after it releases reset. **Open question.**
- **Raw TX** (mode 01): `tx_en = uio_in[2]`, combinational, in either role.
- **Raw RX:** `uio_out[3]` = the synchronised comparator bit, in all modes.
- **uio_out debug pins:**
  - [4] = event open (~8 chips);
  - [5] = LED toggle pulse (1 clock);
  - [6] = servo direction (last sample);
  - [7] = TX sending.
- **7-seg display:**
  - RX: shows `(score-97)*21>>6` as digit 0..9 for ~1.7 s after an event, otherwise '-'. DP = LED state.
  - TX: shows '1'..'3' for the burst being sent, 't' when idle. DP = tx_en.
  - Raw mode: shows 'r'.
- `rx_en = ~role`. sc_phi1/2 run only when rx_en is high: 61 clocks high each, 4-clock dead times, one cycle per 130 clocks.
- Reset: `rst_n` is registered, and every other register uses a synchronous reset.

## Timing alignment (deviation from README, documented in radio_digital.v)
- Sample i is processed at rising edge **E(1 + 130·(i+1))**, where E1 is the first rising edge after rst_n goes high. The README has clock 130·i; the difference comes from one clock for the registered reset and the first tick at div == 129.
- The value used is comp_in as it was 2 edges earlier, because of the 2-flop synchroniser. comp_in must be stable for ≥ 3 clocks before each tick.
- The testbench changes comp_in on the falling edge after each tick and reads trim_out on the falling edge after the next tick.
- Everything else matches the contract bit-exactly. Scores are computed sequentially in 127 clocks, by rotating the selected phase register through its MSB. The score is ready 128 clocks after the window-end tick, so before the next tick, and it keeps that tick's chip count.
- There is no absolute chip counter. The RTL uses ages in chips instead:
  - pair window = history age 197..201 or 388..392 at close;
  - holdoff = chips since the toggle ≥ 9615.

  This is equivalent to the model and has no wrap-around.
- The chip registers aren't reset. Instead, 127 zeros are shifted in after reset, which finishes before the first window end.

## Test results (icarus, cocotb 2.1; 13/13 pass; `grep -c '<failure' results.xml` = 0)
Note: the PLAN.md check `! grep -q failure results.xml` is wrong because `failures="0"` matches it. Use `'<failure'`.

| Test | Result |
|---|---|
| rx_clean, rx_holdoff, rx_two_sends, rx_strong, rx_weak, rx_wrong_code, rx_bursty, rx_fading, rx_no_signal | **PASS, exact.** trim_out matches after every sample (0 mismatches). Event (chip time, max score) lists and LED toggle chip times equal the vectors, and the final DP = LED |
| test_tx_codes | PASS. Codes 0, 0x5A, 126, 127, 1, 0x11: tx_en at every chip centre of the 573-chip send matches tx_codes.npz (bursts plus 64-chip gaps). The send ends, the precomputed LFSR2 start matches `lfsr2`, the 7-seg shows 1/2/3, and there is no resend for 60 chips |
| test_tx_code_change | PASS. A bounce (0x33 for 20 chips, then 0x2C) gives a new send with code 0x2C, starting 48.5 chips after the last change |
| test_raw_and_straps | PASS. With magic + 01, raw TX follows uio_in[2]. uio_out[3] = comp after 2 clocks. uio_oe is 0 in reset and F8 after. Without the magic it stays in code mode |
| test_sc_phases | PASS. No overlap, period 130, ≥ 4 dead clocks |

The full run takes ~11.5 min of wall time (rx_two_sends alone is 5.4 min). Lint (`verilog/rtl/lint.sh`, verilator -Wall) is clean.

## Size (yosys synth → sky130_fd_sc_hd tt_025C_1v80, dfflibmap + abc)
| Block | FFs | Cell area (µm²) | Placed @ 60% (µm²) |
|---|---|---|---|
| RX correlator `rd_corr` (4 × 127 chip regs, majority counters, popcount) | 546 (508 edfxtp) | 16,925 | 28,200 |
| RX control `rd_rx` (servo, events, pairing, holdoff, display timer) | 74 | 3,381 | 5,630 |
| Gold LFSRs + precompute `rd_gold` | 35 | 1,386 | 2,310 |
| TX `rd_tx` | 13 | 562 | 940 |
| Top: syncs, divider, sc phases, debounce, straps, 7-seg, uio | 48 | 2,072 | 3,450 |
| **Total** | **716** (525 enable-FF + 191 plain) | **24,326** | **~40,500** (e.g. 225 × 180 µm) |

80% of the area is sequential.

**Flag:** ~40,500 µm² placed is **~54% of the 75,000 µm² 2×2 tile**, which leaves too little room for the analog blocks. The 508 chip-register bits are 63% of the total.

Suggested reductions (cell area; placed ≈ /0.6):
1. **Clock-gate each phase register** with `sky130_fd_sc_hd__dlclkp` (4 ICGs). The enable flops (edfxtp, 30 µm²) become plain dfxtp (20 µm²). This saves about −5,000 µm² (−8,400 placed) with no functional change.
2. **2 phases (0, 4) instead of 4:** saves about −7,600 µm². The worst-case chip-timing error grows from 1/8 to 1/4 chip, so re-run model/e2e.py to check sensitivity first.
3. 1 + 2 together bring the correlator to ~6,500 µm², the total to ~14,000 µm² cell, and the placed area to **~23,000 µm² (~31% of the tile)**.
4. Smaller items (~0.5–1k): count the 14-bit hold/display timers in 16-chip units; drop the code synchroniser on the RX side.
5. ABC picked a few lpflow iso cells. OpenLane's dont_use list will replace them (negligible).

## Data mode (not implemented): rough extra size
| Part | FFs | Cell µm² |
|---|---|---|
| Gold sync detect: reuse the correlator and its threshold; the winning phase and tick give bit timing | ~10 | ~400 |
| Manchester RX: two half-bit 1s counters + bit/half timer | ~25 | ~800 |
| CRC-8 (shared TX/RX) + length/byte counters | ~20 | ~700 |
| UART TX + RX to the RP2350 (baud divider, shift, bit count) | ~40 | ~1,300 |
| Control FSMs, 3× repeat, Manchester TX | ~30 | ~1,100 |
| **Subtotal, streaming** (the RX forwards bytes plus a CRC-ok flag; the TX reuses the idle RX chip registers as its packet buffer for the 3 repeats) | **~125** | **~4,500 (≈ 7,500 placed)** |
| Optional dedicated 16-byte RX buffer (to drop bad-CRC copies on chip) | +128 | +3,500 (+5,800 placed) |

## Open questions
- **Mode-select strap:** uio[7:4] are outputs after reset. This needs the RP2350 to release them, or else a UART magic command once data mode exists. It is also unknown whether floating TT uio pads read 1010 at reset; that is unlikely, but unverified.
- **Raw TX:** keys `tx_en` in either role. The trim servo keeps running in raw mode. A register-set or frozen trim (docs/slicer.md) is not implemented.
- **Precompute latency:** for code 127 the LFSR2 precompute takes 127 clocks, which only just fits before the first window end (~260 clocks). An RX code change re-adopts after 50 ms, and correlations during the next 127 clocks are invalid. Harmless.
- **Verilator:** the Makefile has a verilator path (`--public-flat-rw`) that hasn't been tried. It would make the RX vectors much faster.
