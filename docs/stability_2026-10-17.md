# Chain stability with the real VDPWR decap (2026-10-17)

`sim/chain/stability.sh` put an ideal 30 pF (the planned VDPWR decap) between chip VDPWR and chip ground.
The decap that fits the tile is 10.6 pF (`decap_vdpwr`, the laid-out devices; `sim/decap/decap_ac.sh`:
10.56 pF, ESR 0.18 Ohm, flat to 434 MHz), which moves the supply resonance with 2 nH from ~650 MHz to
~1.1 GHz. The script now uses the real `decap_vdpwr` subckt by default (`CDEC=<value>` for an ideal C);
this reruns the 2026-10-13 sets both ways.

Setup: tb_chain from `xschem/tb_chain.sch`, magic / netgen / xschem / ngspice 47 built from source, sky130A
1689ac3f. The ideal-30 pF runs reproduce the documented numbers (tt 76.68 dB at 434 MHz, peak 76.93 dB).
Kick: 1 uA, 1 ns into pad_p; growth = late / early output p-p (< 1 decays). Ccpl from out_p to pad_p.

| condition | supply L | Ccpl | growth, real | growth, 30 pF | 434 MHz gain, real / 30 pF (dB) | AC peak, real / 30 pF (dB) | VDPWR p-p after kick, real / 30 pF |
|---|---|---|---|---|---|---|---|
| ss, 10 °C, 1.8 V | 0 | 0 | 1.9e-10 | 2.4e-10 | 81.19 / 81.19 | 81.36 / 81.36 | 0.00175 / 0.00176 uV |
| ss, 10 °C, 1.8 V | 2n | 0 | 2.2e-10 | 1.8e-10 | 81.19 / 81.19 | 81.36 / 81.36 | 17.8 / 2.1 uV |
| ss, 10 °C, 1.8 V | 2n | 0.01f | 1.9e-10 | 1.6e-10 | 81.21 / 81.21 | 81.32 / 81.32 | 17.8 / 2.12 uV |
| ss, 10 °C, 1.8 V | 2n | 0.1f | 2.2e-10 | 2.2e-10 | 81.21 / 81.21 | 81.58 / 81.58 | 17.9 / 2.69 uV |
| ss, 10 °C, 1.8 V | 2n | 1f | 0.99 | 0.99 | 74.41 / 74.41 | 76.68 / 76.68 | 1.4e+03 / 1.2e+03 uV |
| ss, 10 °C, 1.8 V | 5n | 0 | 2.9e-10 | 1.3e-09 | 81.19 / 81.19 | 81.36 / 81.36 | 8.31 / 17.9 uV |
| ss, 10 °C, 1.8 V | 5n | 0.1f | 2e-10 | 1.4e-09 | 81.21 / 81.21 | 81.58 / 81.58 | 8.01 / 23.1 uV |
| ss, 10 °C, 1.8 V | 5n | 1f | 0.99 | 0.99 | 74.41 / 74.41 | 76.68 / 76.68 | 3.4e+03 / 3.38e+03 uV |
| ss, 10 °C, 1.89 V | 0 | 0 | 2.4e-10 | 3.1e-10 | 81.49 / 81.49 | 81.66 / 81.66 | 0.00194 / 0.00195 uV |
| ss, 10 °C, 1.89 V | 2n | 0 | 2.4e-10 | 2.4e-10 | 81.49 / 81.49 | 81.66 / 81.66 | 15.9 / 1.81 uV |
| ss, 10 °C, 1.89 V | 2n | 0.1f | 2.5e-10 | 2.3e-10 | 81.48 / 81.48 | 81.89 / 81.89 | 16 / 3.05 uV |
| tt, 27 °C, 1.8 V | 0 | 0 | 1.6e-10 | 1.9e-10 | 76.68 / 76.68 | 76.93 / 76.93 | 0.000669 / 0.000672 uV |
| tt, 27 °C, 1.8 V | 2n | 0 | 2e-10 | 1.7e-10 | 76.68 / 76.68 | 76.93 / 76.93 | 6.14 / 0.991 uV |
| tt, 27 °C, 1.8 V | 2n | 0.01f | 1.5e-10 | 2e-10 | 76.70 / 76.70 | 76.90 / 76.90 | 6.13 / 0.977 uV |
| tt, 27 °C, 1.8 V | 2n | 0.1f | 1.5e-10 | 1.7e-10 | 76.83 / 76.83 | 76.84 / 76.84 | 6.1 / 0.866 uV |
| tt, 27 °C, 1.8 V | 2n | 1f | 1 | 1 | 73.64 / 73.64 | 83.29 / 83.29 | 344 / 291 uV |
| tt, 27 °C, 1.8 V | 5n | 0 | 1.9e-10 | 4.7e-10 | 76.68 / 76.68 | 76.93 / 76.93 | 3.48 / 5.5 uV |
| tt, 27 °C, 1.8 V | 5n | 0.1f | 1.9e-10 | 4.3e-10 | 76.83 / 76.83 | 76.84 / 76.84 | 3.09 / 6.28 uV |
| tt, 27 °C, 1.8 V | 5n | 1f | 1 | 1 | 73.64 / 73.64 | 83.29 / 83.29 | 748 / 693 uV |

**Result:** same as with 30 pF. Every case decays up to 0.1 fF of output -> input coupling; 1 fF rings
(growth 0.992-0.996, below 1 but barely; the same as with 30 pF and as on 2026-10-13). Gain and AC peaking agree to 0.01 dB. The decap does change the
supply (VDPWR p-p after the kick differs), but at microvolts it doesn't reach the chain: the chain's
stability doesn't depend on the decap value in this range.

Not in this bench: other loads and aggressors on VDPWR (the digital macro and its std-cell decaps, the TX
ring); the extracted-tile sims (`sim/top/tb_tile*.py`) have the real decaps from the layout.

Rerun (from build/real after netlisting tb_chain there):
`bash ../../sim/chain/stability.sh`, `CORNER=ss TEMP=10 bash ../../sim/chain/stability.sh`,
`VSUP=1.89 CORNER=ss TEMP=10 CASES='0:0 2n:0 2n:0.1f' bash ../../sim/chain/stability.sh`; add `CDEC=30p` for the old setup.
