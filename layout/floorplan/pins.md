# Floorplan: block positions and pin positions

Generated from the floorplan page's variant **RX in the corner (ua[3] / ua[2]), TX on ua[4] / ua[5]** by `layout/floorplan/page/pinreport.js`; the placements are also in `floorplan.json` next to this file.

- Coordinates in µm. **Placement**: lower-left of the placed (transformed) bbox in the tile, and the GDS orientation (KLayout `DCplxTrans(1, rot, mirror, …)`, mirror about x first).
- **Pins**: in each block's *own* frame (its bbox lower-left = 0, 0, before the orientation), grouped by the block's own edge. "moved" = a new position for the re-layout / re-harden; the others are where the GDS has them now. The tile direction each edge faces after placement is given in brackets.
- Moved pins sit on the edge facing what they connect to (`pinfit.js`). Positions along an edge are targets: pins closer than ~1 µm were spread to 1 µm.

## Checks (with the moved pins)

| rule | status | value |
|---|---|---|
| 1. Chain input far from the macro | pass | 159 µm |
| 2. Late stages away from the input | fail | 4 µm |
| 3. Clock edges off the RX | pass | 31 µm |
| 4. Short analog path | pass | 164 µm |
| 5. TX at ua[4] / ua[5] | pass | 15 µm |
| 6. Bias next to the chain | fail | 123 µm |
| 7. Decap VAPWR | pass | 111 % |
| 7. Decap VDPWR | pass | 109 % |
| 8. TX away from the RX input | warn | 3 µm |
| 9. Overlaps and spacing | pass | none |
| 9. TT pin channel clear | fail | 2.9 µm |
| P. Power straps | fail | 1 blocked |

## macro (radio_digital)

- Size: 200.00 × 220.00 (reshaped from 260 × 190, 44000.00 µm² vs 49400: re-harden at this size)
- Placement: x 282.50, y 2.88, MY (rot 180, mirror true)
- Pins moved: 57

**E edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| rx_en | 199.75 | 7.14 | moved |
| comp_in | 199.75 | 86.02 | moved |
| trim_out[7] | 199.75 | 94.18 | moved |
| trim_out[6] | 199.75 | 102.34 | moved |
| trim_out[5] | 199.75 | 109.14 | moved |
| trim_out[4] | 199.75 | 117.30 | moved |
| trim_out[3] | 199.75 | 124.10 | moved |
| trim_out[2] | 199.75 | 132.26 | moved |
| trim_out[1] | 199.75 | 139.06 | moved |
| trim_out[0] | 199.75 | 154.02 | moved |
| sc_phi2 | 199.75 | 155.38 | moved |
| sc_phi1 | 199.75 | 156.74 | moved |
| dbg_en | 199.75 | 158.10 | moved |
| tx_en_n | 199.75 | 159.46 | moved |
| tx_en | 199.75 | 160.82 | moved |
| clk | 199.75 | 162.18 | moved |
| uio_oe[7] | 199.75 | 163.54 | moved |
| uio_oe[6] | 199.75 | 164.90 | moved |
| uio_oe[5] | 199.75 | 166.26 | moved |
| uio_oe[4] | 199.75 | 167.62 | moved |
| uio_oe[3] | 199.75 | 168.98 | moved |
| uio_oe[2] | 199.75 | 170.34 | moved |
| uio_oe[1] | 199.75 | 171.70 | moved |
| uio_oe[0] | 199.75 | 173.06 | moved |
| uio_out[7] | 199.75 | 174.42 | moved |
| uio_out[6] | 199.75 | 175.78 | moved |
| uio_out[5] | 199.75 | 177.14 | moved |
| uio_out[4] | 199.75 | 178.50 | moved |
| uio_out[3] | 199.75 | 179.86 | moved |
| uio_out[2] | 199.75 | 181.22 | moved |
| uio_out[1] | 199.75 | 182.58 | moved |
| uio_out[0] | 199.75 | 183.94 | moved |
| uo_out[7] | 199.75 | 185.30 | moved |
| uo_out[6] | 199.75 | 186.66 | moved |
| uo_out[5] | 199.75 | 188.02 | moved |
| uo_out[4] | 199.75 | 189.38 | moved |
| uo_out[3] | 199.75 | 190.74 | moved |
| uo_out[2] | 199.75 | 192.10 | moved |
| uo_out[1] | 199.75 | 193.46 | moved |
| uo_out[0] | 199.75 | 194.82 | moved |
| uio_in[7] | 199.75 | 196.18 | moved |
| uio_in[6] | 199.75 | 197.54 | moved |
| uio_in[5] | 199.75 | 198.90 | moved |
| uio_in[4] | 199.75 | 200.26 | moved |
| uio_in[3] | 199.75 | 201.62 | moved |
| uio_in[2] | 199.75 | 202.98 | moved |
| uio_in[1] | 199.75 | 204.34 | moved |
| uio_in[0] | 199.75 | 205.70 | moved |
| ui_in[7] | 199.75 | 207.06 | moved |
| ui_in[6] | 199.75 | 208.42 | moved |
| ui_in[5] | 199.75 | 209.78 | moved |
| ui_in[4] | 199.75 | 211.14 | moved |
| ui_in[3] | 199.75 | 212.50 | moved |
| ui_in[2] | 199.75 | 213.86 | moved |
| ui_in[1] | 199.75 | 215.22 | moved |
| ui_in[0] | 199.75 | 216.58 | moved |
| rst_n | 199.75 | 217.94 | moved |

## xchain (lna_chain_t)

- Size: 123.53 × 63.50 (GDS)
- Placement: x 74.84, y 6.50, R0 (rot 0, mirror false)
- Pins moved: none

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 44.43 | 62.75 |  |
| o1n | 62.58 | 63.25 |  |
| o1p | 63.98 | 63.25 |  |
| o2n | 74.98 | 63.25 |  |
| o2p | 76.38 | 63.25 |  |
| o3n | 86.68 | 63.25 |  |
| o3p | 88.08 | 63.25 |  |
| o4n | 98.38 | 63.25 |  |
| o4p | 99.78 | 63.25 |  |
| o5n | 110.08 | 63.25 |  |
| o5p | 111.48 | 63.25 |  |
| outn | 121.78 | 63.25 |  |
| outp | 123.18 | 63.25 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| inp | 8.14 | 0.20 |  |
| inn | 25.62 | 0.20 |  |
| vcm | 36.26 | 0.25 |  |
| ibias | 42.33 | 0.25 |  |
| VSS | 43.68 | 31.75 |  |
| lna_lo_n | 74.28 | 0.25 |  |

## xbias (bias_gen)

- Size: 80.22 × 49.07 (GDS)
- Placement: x 206.70, y 3.00, R90 (rot 90, mirror false)
- Pins moved: none

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| ib_chain | 28.18 | 48.82 |  |
| vcm | 31.32 | 48.82 |  |
| ib_det | 79.22 | 48.82 |  |

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| en | 2.00 | 0.25 |  |
| tail | 14.10 | 12.85 |  |
| VSS | 15.18 | 0.75 |  |
| d1 | 15.64 | 9.65 |  |
| dsw | 28.30 | 14.45 |  |
| pb | 28.30 | 13.65 |  |
| tsw | 28.30 | 10.45 |  |
| vref | 28.30 | 11.25 |  |
| x | 28.30 | 8.85 |  |
| rd0 | 33.48 | 17.44 |  |
| rd1 | 34.48 | 6.37 |  |
| rd3 | 36.48 | 6.37 |  |
| rd4 | 37.48 | 17.44 |  |
| rd6 | 39.48 | 17.44 |  |
| rd7 | 40.48 | 6.37 |  |
| rt0 | 44.16 | 17.15 |  |
| rt1 | 45.16 | 6.65 |  |
| rt2 | 46.16 | 17.15 |  |
| xr | 49.92 | 17.67 |  |

**W edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| enb | 6.51 | 11.25 |  |
| ota | 2.05 | 12.05 |  |
| pr | 2.05 | 15.25 |  |
| VDD | 15.18 | 23.05 |  |

**E edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ib_comp | 80.02 | 48.07 |  |

## xdet (log_det)

- Size: 137.05 × 16.11 (GDS)
- Placement: x 67.14, y 76.90, R0 (rot 0, mirror false)
- Pins moved: none

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 10.65 | 15.86 |  |
| t1p | 13.77 | 8.12 |  |
| t1n | 24.83 | 8.12 |  |
| t2p | 34.59 | 8.12 |  |
| t2n | 45.66 | 8.12 |  |
| t3p | 55.43 | 8.12 |  |
| t3n | 66.49 | 8.12 |  |
| t4p | 76.25 | 8.12 |  |
| t4n | 87.32 | 8.12 |  |
| t5p | 97.09 | 8.12 |  |
| t5n | 108.15 | 8.12 |  |
| t6p | 117.92 | 8.12 |  |
| t6n | 128.98 | 8.12 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VSS | 0.50 | 0.60 |  |
| det | 0.25 | 2.10 |  |
| ibias_det | 0.25 | 2.80 |  |

## xlpf (lpf_rc)

- Size: 65.20 × 35.02 (GDS)
- Placement: x 67.20, y 95.60, R0 (rot 0, mirror false)
- Pins moved: none

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| r1 | 24.20 | 32.62 |  |
| r3 | 26.20 | 32.62 |  |
| r5 | 28.20 | 32.62 |  |
| r7 | 30.20 | 32.62 |  |
| r9 | 32.20 | 32.62 |  |
| r11 | 34.20 | 32.62 |  |
| r13 | 36.20 | 32.62 |  |
| r15 | 38.20 | 32.62 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| in | 1.50 | 0.25 |  |
| r2 | 25.20 | 5.58 |  |
| r4 | 27.20 | 5.58 |  |
| r6 | 29.20 | 5.58 |  |
| r8 | 31.20 | 5.58 |  |
| r10 | 33.20 | 5.58 |  |
| r12 | 35.20 | 5.58 |  |
| r14 | 37.20 | 5.58 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VSS | 0.50 | 1.00 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| out | 64.95 | 31.00 |  |

## xavg (avg_sc)

- Size: 77.35 × 30.40 (GDS)
- Placement: x 55.00, y 133.20, R0 (rot 0, mirror false)
- Pins moved: none

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| phi1 | 65.00 | 30.15 |  |
| phi2 | 65.70 | 30.15 |  |
| phi1b | 67.71 | 24.75 |  |
| VDD | 68.52 | 29.65 |  |
| phi2b | 68.91 | 25.55 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| in | 77.10 | 0.25 |  |
| VSS | 68.52 | 15.55 |  |
| cs | 70.06 | 21.55 |  |
| out | 77.10 | 22.35 |  |

## xcomp (comp_ct)

- Size: 73.55 × 41.16 (GDS)
- Placement: x 135.00, y 122.00, MYR90 (rot 270, mirror true)
- Pins moved: none

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| d1 | 18.65 | 33.31 |  |
| tail | 27.30 | 30.91 |  |
| vref | 28.60 | 30.11 |  |
| d2 | 36.90 | 31.71 |  |
| VDD | 37.00 | 40.41 |  |
| inp | 37.85 | 40.91 |  |
| sa | 40.30 | 32.52 |  |
| inn | 42.45 | 40.91 |  |
| sb | 44.45 | 29.31 |  |

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| rdeg4 | 6.08 | 5.60 |  |
| rdeg6 | 8.09 | 5.60 |  |
| rdeg8 | 10.09 | 5.60 |  |
| rdeg10 | 12.09 | 5.60 |  |
| rdeg12 | 14.09 | 5.60 |  |
| rdeg14 | 16.09 | 5.60 |  |
| rdeg15 | 17.09 | 16.68 |  |
| rdeg16 | 18.09 | 5.60 |  |
| rdeg17 | 19.09 | 16.68 |  |
| rdeg18 | 20.09 | 5.60 |  |
| rdeg19 | 21.09 | 16.68 |  |
| rdeg20 | 22.09 | 5.60 |  |
| rdeg21 | 23.09 | 16.68 |  |
| rdeg22 | 24.09 | 5.60 |  |
| rdeg23 | 25.09 | 16.68 |  |
| rdeg24 | 26.09 | 5.60 |  |
| rdeg25 | 27.09 | 16.68 |  |
| rdeg26 | 28.09 | 5.60 |  |
| rdeg27 | 29.09 | 16.68 |  |
| rdeg28 | 30.09 | 5.60 |  |
| rdeg29 | 31.09 | 16.68 |  |
| VSS | 37.00 | 19.71 |  |
| out | 71.60 | 0.25 |  |

**W edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| rdeg2 | 4.08 | 5.60 |  |
| rdeg1 | 3.08 | 16.68 |  |
| rdeg11 | 13.09 | 16.68 |  |
| rdeg13 | 15.09 | 16.68 |  |
| rdeg3 | 5.08 | 16.68 |  |
| rdeg5 | 7.08 | 16.68 |  |
| rdeg7 | 9.09 | 16.68 |  |
| rdeg9 | 11.09 | 16.68 |  |

**E edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| trim | 73.20 | 19.47 |  |
| ibias | 73.20 | 22.47 |  |
| o2 | 69.34 | 33.31 |  |

## xdac (r2r)

- Size: 71.75 × 54.12 (GDS)
- Placement: x 179.00, y 95.60, MYR90 (rot 270, mirror true)
- Pins moved: none

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| b0 | 5.62 | 0.50 |  |
| VGND | 13.12 | 0.50 |  |
| b | 17.12 | 2.50 |  |
| b1 | 20.62 | 0.50 |  |
| c | 24.62 | 2.50 |  |
| b2 | 28.12 | 0.50 |  |
| d | 32.12 | 2.50 |  |
| b3 | 35.62 | 0.50 |  |
| e | 39.62 | 2.50 |  |
| b4 | 43.12 | 0.50 |  |
| f | 47.12 | 2.50 |  |
| b5 | 50.62 | 0.50 |  |
| g | 54.62 | 2.50 |  |
| b6 | 58.12 | 0.50 |  |
| out | 62.12 | 0.50 |  |
| b7 | 65.62 | 0.50 |  |

## xctrim (ctrim_1p)

- Size: 22.43 × 22.43 (GDS)
- Placement: x 150.00, y 95.60, MX (rot 0, mirror true)
- Pins moved: none

**S edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| trim | 1.00 | 0.25 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VGND | 0.25 | 11.22 |  |

## xdbg (dbg_tg)

- Size: 5.70 × 16.30 (GDS)
- Placement: x 59.00, y 95.00, MY (rot 180, mirror true)
- Pins moved: none

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 2.83 | 15.30 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 2.83 | 1.00 |  |

**W edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| a | 0.25 | 0.25 |  |
| enb | 2.74 | 7.15 |  |

**E edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| b | 5.55 | 0.25 |  |
| en | 5.45 | 6.35 |  |

## xtx.xring (tx_ring)

- Size: 18.32 × 6.96 (GDS)
- Placement: x 37.00, y 65.00, R0 (rot 0, mirror false)
- Pins moved: none

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| r22 | 3.64 | 5.01 |  |
| r21 | 5.02 | 5.01 |  |
| r20 | 6.86 | 5.01 |  |
| r19 | 8.24 | 5.01 |  |
| r18 | 9.62 | 5.01 |  |
| r17 | 11.00 | 5.01 |  |
| r16 | 12.38 | 5.01 |  |
| r15 | 13.76 | 5.01 |  |
| r14 | 15.14 | 5.01 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| r2 | 2.72 | 1.95 |  |
| r3 | 4.10 | 1.95 |  |
| r4 | 5.48 | 1.95 |  |
| r5 | 6.86 | 1.95 |  |
| r6 | 8.24 | 1.95 |  |
| VDD | 9.16 | 3.48 |  |
| VSS | 9.16 | 0.50 |  |
| r7 | 9.62 | 1.95 |  |
| r8 | 11.00 | 1.95 |  |
| r9 | 12.84 | 1.95 |  |
| r10 | 14.22 | 1.95 |  |
| r11 | 15.60 | 1.95 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| out | 0.44 | 1.56 |  |
| r1 | 1.34 | 1.95 |  |
| en | 0.44 | 4.46 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| r12 | 16.98 | 1.95 |  |
| r13 | 16.52 | 5.01 |  |

## xtx.xls (tx_ls)

- Size: 14.25 × 19.00 (GDS)
- Placement: x 34.50, y 48.00, R270 (rot 270, mirror false)
- Pins moved: none

**N edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 3.95 | 18.00 |  |
| VAPWR | 10.90 | 18.00 |  |

**S edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 7.40 | 1.00 |  |

**W edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ctrl | 6.23 | 10.15 |  |
| in | 1.00 | 10.95 |  |

**E edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ctrl_n | 8.50 | 8.55 |  |
| A | 13.80 | 9.35 |  |
| B | 13.80 | 10.95 |  |

## xtx.xlse_p (tx_ls_en)

- Size: 13.35 × 15.48 (GDS)
- Placement: x 56.50, y 48.00, R270 (rot 270, mirror false)
- Pins moved: none

**N edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 3.50 | 14.48 |  |
| VAPWR | 10.00 | 14.48 |  |

**S edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 6.95 | 1.00 |  |

**W edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ctrl | 5.78 | 7.63 |  |
| in | 1.00 | 8.43 |  |

**E edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ctrl_n | 7.60 | 6.03 |  |
| A | 12.90 | 6.83 |  |
| B | 12.90 | 8.43 |  |

## xtx.xlse_n (tx_ls_en)

- Size: 13.35 × 15.48 (GDS)
- Placement: x 16.50, y 48.00, R270 (rot 270, mirror false)
- Pins moved: none

**N edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 3.50 | 14.48 |  |
| VAPWR | 10.00 | 14.48 |  |

**S edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 6.95 | 1.00 |  |

**W edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ctrl | 5.78 | 7.63 |  |
| in | 1.00 | 8.43 |  |

**E edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ctrl_n | 7.60 | 6.03 |  |
| A | 12.90 | 6.83 |  |
| B | 12.90 | 8.43 |  |

## xtx.xdrv_p (tx_drv)

- Size: 40.90 × 26.68 (GDS)
- Placement: x 45.66, y 4.50, R270 (rot 270, mirror false)
- Pins moved: none

**N edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VAPWR | 20.82 | 25.18 |  |

**S edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 20.82 | 1.50 |  |
| y4 | 22.41 | 12.38 |  |

**W edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| y0 | 3.05 | 10.53 |  |
| in | 1.00 | 11.33 |  |
| y2 | 7.94 | 11.33 |  |
| en | 1.00 | 12.38 |  |
| y1 | 5.89 | 12.38 |  |
| y3 | 10.99 | 12.38 |  |

**E edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| out | 39.40 | 12.08 |  |

## xtx.xdrv_n (tx_drv)

- Size: 40.90 × 26.68 (GDS)
- Placement: x 16.40, y 4.50, MYR90 (rot 270, mirror true)
- Pins moved: none

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VAPWR | 20.82 | 25.18 |  |

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 20.82 | 1.50 |  |
| y4 | 22.41 | 12.38 |  |

**W edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| y0 | 3.05 | 10.53 |  |
| in | 1.00 | 11.33 |  |
| y2 | 7.94 | 11.33 |  |
| en | 1.00 | 12.38 |  |
| y1 | 5.89 | 12.38 |  |
| y3 | 10.99 | 12.38 |  |

**E edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| out | 39.40 | 12.08 |  |

## Straps and decap

- VGND strap: x 12.00, w 3.10 (met4, full height)
- VDPWR strap: x 5.80, w 4.70 (met4, full height)
- VAPWR strap: x 481.00, w 8.22 (met4, full height)
- VGND strap: x 489.72, w 1.20 (met4, full height)
- VDPWR strap: x 491.42, w 1.20 (met4, full height)
- VAPWR strap: x 276.50, w 1.20 (met4, full height)
- VGND strap: x 278.20, w 1.20 (met4, full height)
- VDPWR strap: x 279.90, w 1.20 (met4, full height)
- VAPWR strap: x 0.30, w 5.00 (met4, full height)
- xdeca 1: x 0.00, y 2.00, 13.00 × 95.00
- xdeca 2: x 259.20, y 2.00, 17.80 × 81.00
- xdeca 3: x 135.00, y 198.10, 41.00 × 14.90
- xdeca 4: x 179.00, y 170.00, 54.00 × 43.00
- xdeca 5: x 0.00, y 100.50, 52.00 × 120.50
- xdeca 6: x 236.00, y 86.00, 41.00 × 127.00
- xdeca 7: x 179.00, y 95.60, 54.12 × 71.75 (MIM only, on top of r2r)
- xdecd 1: x 135.00, y 96.00, 12.00 × 22.00
- xdecd 2: x 207.00, y 86.00, 26.00 × 7.00
- xdecd 3: x 16.00, y 65.00, 15.50 × 32.00
- xdecd 4: x 55.00, y 167.00, 77.00 × 46.00
