# Interactive explainer: source

Generates the self-contained [`../explainer.html`](../explainer.html) (one file, no network, ~110 kB) from the simulations, bench data and link model in this repo. Same pattern as [metastability_explorer](https://github.com/mattvenn/metastability_explorer): `template.html` holds the page, and `gendata.py` replaces its `/*__PAYLOAD__*/` token with the data (traces resampled, quantized to 1 byte, gzipped, base64). The browser inflates it with `DecompressionStream('gzip')`.

Open it from the repo: <https://raw.githack.com/mattvenn/ook-asic-radio/main/docs/explainer.html> (githack serves the committed file as a page; GitHub Pages on this repo is the TT GDS viewer).

## Run
```
tools/osic-mac docs/explainer/sims.sh     # ~3 min; tools/osic on Linux. Raws land in build/ (gitignored)
python3 docs/explainer/gendata.py         # ~10 s; writes docs/explainer.html
```
`gendata.py` prints each source and marks any missing raw. That view then shows a "no data" note and the page still builds.

## Sources
| View | Source |
|---|---|
| path loss | `bench/data/sweep2/ota.csv`, fit −44 dBm at 1 m, 1/d^1.89 |
| TX ring, level-shifter A/B, drivers, dipole | `build/tb_tx_ab.raw` from `xschem/tb_tx.sch` (tt, schematic) |
| RX antenna → 6 stages → det (−60 dBm tone, keyed) | `build/rx_rf_tone.raw`, `rx_rf_key.raw` from `sim/rx/rf.sh` |
| log detector transfer, per-tap amplitude | `sim/logdet/taps.txt`, `transfer_cw.txt` |
| baseband det → lpf → avg → comparator, trim (−70 / −94 dBm) | `build/rx_bb_<lvl>.raw` from `sim/rx/gen_det.py` + `sim/rx/bb.sh` |
| sent vs received chips, score, 2-of-3 (follows the distance slider) | `model/` link model at 2 dB steps, −110 to −60 dBm: one send of code 0x5A, NF 11 dB / 450 MHz noise, 2 mV offset, 0.07 mV trim, 0.3 mV comparator noise at 13 mV/dB, bit-exact `radio.RxDigital` |

`sims.sh` stubs `pyvisa` (pulled in through `bench/scope.py`) so `gen_det.py` runs in the osic image.

## Editing
Block text, tour captions and figure choices are in `template.html` (`B`, `TOUR`, `fig*` functions). Rebuild with `gendata.py` after editing.
