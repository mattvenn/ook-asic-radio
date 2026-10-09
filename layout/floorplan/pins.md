# Floorplan: block positions and pin positions

Generated from the floorplan page's variant **matt layout 4 (handoff)** by `layout/floorplan/page/pinreport.js`; the placements are also in `floorplan.json` next to this file.

- Coordinates in µm. **Placement**: lower-left of the placed (transformed) bbox in the tile, and the GDS orientation (KLayout `DCplxTrans(1, rot, mirror, …)`, mirror about x first).
- **Pins**: in each block's *own* frame (its bbox lower-left = 0, 0, before the orientation), grouped by the block's own edge. "moved" = a new position for the re-layout / re-harden; the others are where the GDS has them now. The tile direction each edge faces after placement is given in brackets.
- Moved pins sit on the edge facing what they connect to (`pinfit.js`). Positions along an edge are targets: pins closer than ~1 µm were spread to 1 µm.

## Checks (with the moved pins)

| rule | status | value |
|---|---|---|
| 1. Chain input far from the macro | pass | 141 µm |
| 2. Late stages away from the input | fail | 0 µm |
| 3. Clock edges off the RX | pass | 25 µm |
| 4. Short analog path | pass | 48 µm |
| 5. TX at ua[3] / ua[4] | fail | 121 µm |
| 6. Bias next to the chain | pass | 6 µm |
| 7. Decap VAPWR | warn | 97 % |
| 7. Decap VDPWR | pass | 102 % |
| 8. TX away from the RX input | warn | 39 µm |
| 9. Overlaps and spacing | pass | none |
| 9. TT pin channel clear | fail | 2.9 µm |
| P. Power straps | pass | 8 clear |

## macro (radio_digital)

- Size: 200.00 × 220.00 (reshaped from 260 × 190, 44000.00 µm² vs 49400: re-harden at this size)
- Placement: x 282.50, y 2.88, MY (rot 180, mirror true)
- Pins moved: 57

**E edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| rx_en | 199.75 | 6.60 | moved |
| trim_out[0] | 199.75 | 52.74 | moved |
| trim_out[1] | 199.75 | 67.74 | moved |
| comp_in | 199.75 | 73.72 | moved |
| trim_out[2] | 199.75 | 75.24 | moved |
| trim_out[3] | 199.75 | 82.74 | moved |
| dbg_en | 199.75 | 86.47 | moved |
| trim_out[4] | 199.75 | 90.24 | moved |
| tx_en_n | 199.75 | 92.47 | moved |
| trim_out[5] | 199.75 | 97.74 | moved |
| tx_en | 199.75 | 103.26 | moved |
| trim_out[6] | 199.75 | 105.24 | moved |
| trim_out[7] | 199.75 | 126.47 | moved |
| sc_phi2 | 199.75 | 147.10 | moved |
| sc_phi1 | 199.75 | 148.10 | moved |
| clk | 199.75 | 178.00 | moved |
| uio_oe[7] | 199.75 | 179.00 | moved |
| uio_oe[6] | 199.75 | 180.00 | moved |
| uio_oe[5] | 199.75 | 181.00 | moved |
| uio_oe[4] | 199.75 | 182.00 | moved |
| uio_oe[3] | 199.75 | 183.00 | moved |
| uio_oe[2] | 199.75 | 184.00 | moved |
| uio_oe[1] | 199.75 | 185.00 | moved |
| uio_oe[0] | 199.75 | 186.00 | moved |
| uio_out[7] | 199.75 | 187.00 | moved |
| uio_out[6] | 199.75 | 188.00 | moved |
| uio_out[5] | 199.75 | 189.00 | moved |
| uio_out[4] | 199.75 | 190.00 | moved |
| uio_out[3] | 199.75 | 191.00 | moved |
| uio_out[2] | 199.75 | 192.00 | moved |
| uio_out[1] | 199.75 | 193.00 | moved |
| uio_out[0] | 199.75 | 194.00 | moved |
| uo_out[7] | 199.75 | 195.00 | moved |
| uo_out[6] | 199.75 | 196.00 | moved |
| uo_out[5] | 199.75 | 197.00 | moved |
| uo_out[4] | 199.75 | 198.00 | moved |
| uo_out[3] | 199.75 | 199.00 | moved |
| uo_out[2] | 199.75 | 200.00 | moved |
| uo_out[1] | 199.75 | 201.00 | moved |
| uo_out[0] | 199.75 | 202.00 | moved |
| uio_in[7] | 199.75 | 203.00 | moved |
| uio_in[6] | 199.75 | 204.00 | moved |
| uio_in[5] | 199.75 | 205.00 | moved |
| uio_in[4] | 199.75 | 206.00 | moved |
| uio_in[3] | 199.75 | 207.00 | moved |
| uio_in[2] | 199.75 | 208.00 | moved |
| uio_in[1] | 199.75 | 209.00 | moved |
| uio_in[0] | 199.75 | 210.00 | moved |
| ui_in[7] | 199.75 | 211.00 | moved |
| ui_in[6] | 199.75 | 212.00 | moved |
| ui_in[5] | 199.75 | 213.00 | moved |
| ui_in[4] | 199.75 | 214.00 | moved |
| ui_in[3] | 199.75 | 215.00 | moved |
| ui_in[2] | 199.75 | 216.00 | moved |
| ui_in[1] | 199.75 | 217.00 | moved |
| ui_in[0] | 199.75 | 218.00 | moved |
| rst_n | 199.75 | 219.00 | moved |

## xchain (lna_chain)

- Size: 134.06 × 70.52 (GDS)
- Placement: x 21.00, y 6.50, MX (rot 0, mirror true)
- Pins moved: 2

**N edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| inp | 3.60 | 70.27 |  |
| inn | 36.76 | 70.27 |  |
| o1n | 106.42 | 53.57 |  |
| o1p | 106.42 | 52.87 |  |

**S edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| o5n | 31.54 | 16.95 |  |
| o5p | 31.54 | 17.65 |  |
| o4n | 64.08 | 16.95 |  |
| o4p | 64.08 | 17.65 |  |
| o3n | 96.62 | 16.95 |  |
| o3p | 96.62 | 17.65 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VDD | 0.50 | 14.80 |  |
| outn | 0.30 | 16.25 |  |
| outp | 0.30 | 17.65 |  |
| VSS | 0.50 | 36.01 |  |
| g1n | 7.04 | 61.01 |  |
| g1p | 6.04 | 61.01 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| o2n | 129.16 | 16.95 |  |
| o2p | 129.16 | 17.65 |  |
| vcm | 133.81 | 38.20 | moved |
| ibias | 133.81 | 41.34 | moved |

## xbias (bias_gen)

- Size: 80.22 × 49.07 (GDS)
- Placement: x 160.50, y 7.50, R90 (rot 90, mirror false)
- Pins moved: 5

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| ib_chain | 28.18 | 48.82 | moved |
| vcm | 31.32 | 48.82 | moved |
| ib_det | 79.22 | 48.82 | moved |

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| en | 2.05 | 0.25 | moved |
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
| ib_comp | 79.97 | 48.07 | moved |

## xdet (log_det)

- Size: 87.33 × 31.01 (GDS)
- Placement: x 67.50, y 80.00, MX (rot 0, mirror true)
- Pins moved: 2

**N edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| t1n | 12.77 | 23.02 |  |
| t2p | 22.53 | 23.02 |  |
| t2n | 33.59 | 23.02 |  |
| t3p | 43.36 | 23.02 |  |
| t3n | 54.43 | 23.02 |  |

**S edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| det | 1.00 | 0.25 | moved |
| t4n | 12.77 | 7.99 |  |
| t5p | 22.53 | 7.99 |  |
| t5n | 33.59 | 7.99 |  |
| t6p | 43.36 | 7.99 |  |
| t6n | 54.43 | 7.99 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| t4p | 1.70 | 7.99 |  |
| VSS | 0.50 | 15.51 |  |
| t1p | 1.70 | 23.02 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VDD | 86.73 | 15.51 |  |
| ibias_det | 87.08 | 24.29 | moved |

## xlpf (lpf_rc)

- Size: 65.20 × 35.02 (GDS)
- Placement: x 67.00, y 113.60, R0 (rot 0, mirror false)
- Pins moved: 2

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
| in | 1.50 | 0.25 | moved |
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
| out | 64.95 | 34.02 | moved |

## xavg (avg_sc)

- Size: 77.35 × 30.40 (GDS)
- Placement: x 53.00, y 151.20, R0 (rot 0, mirror false)
- Pins moved: 4

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| phi1b | 67.71 | 24.75 |  |
| VDD | 68.52 | 29.65 |  |
| phi2b | 68.91 | 25.55 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| in | 76.35 | 0.25 | moved |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| phi2 | 77.10 | 1.00 | moved |
| VSS | 68.52 | 15.55 |  |
| phi1 | 77.10 | 19.15 | moved |
| out | 77.10 | 20.15 | moved |
| cs | 70.06 | 21.55 |  |

## xcomp (comp_ct)

- Size: 73.45 × 41.97 (GDS)
- Placement: x 137.50, y 116.60, R90 (rot 90, mirror false)
- Pins moved: 5

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| d1 | 18.65 | 33.31 |  |
| tail | 27.30 | 29.32 |  |
| vref | 28.60 | 31.71 |  |
| inp | 31.02 | 41.72 | moved |
| inn | 35.60 | 41.72 | moved |
| d2 | 36.90 | 30.92 |  |
| VDD | 37.00 | 41.22 |  |
| sa | 40.30 | 32.52 |  |
| sb | 44.45 | 28.52 |  |

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| out | 1.00 | 0.25 | moved |
| rdeg4 | 6.08 | 5.61 |  |
| rdeg6 | 8.09 | 5.61 |  |
| rdeg8 | 10.09 | 5.61 |  |
| rdeg10 | 12.09 | 5.61 |  |
| rdeg12 | 14.09 | 5.61 |  |
| rdeg14 | 16.09 | 5.61 |  |
| rdeg15 | 17.09 | 16.69 |  |
| rdeg16 | 18.09 | 5.61 |  |
| rdeg17 | 19.09 | 16.69 |  |
| rdeg18 | 20.09 | 5.61 |  |
| rdeg19 | 21.09 | 16.69 |  |
| rdeg20 | 22.09 | 5.61 |  |
| rdeg21 | 23.09 | 16.69 |  |
| rdeg22 | 24.09 | 5.61 |  |
| rdeg23 | 25.09 | 16.69 |  |
| rdeg24 | 26.09 | 5.61 |  |
| rdeg25 | 27.09 | 16.69 |  |
| rdeg26 | 28.09 | 5.61 |  |
| rdeg27 | 29.09 | 16.69 |  |
| rdeg28 | 30.09 | 5.61 |  |
| rdeg29 | 31.09 | 16.69 |  |
| VSS | 37.00 | 19.72 |  |

**W edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| rdeg2 | 4.08 | 5.61 |  |
| rdeg1 | 3.08 | 16.69 |  |
| rdeg11 | 13.09 | 16.69 |  |
| rdeg13 | 15.09 | 16.69 |  |
| rdeg3 | 5.08 | 16.69 |  |
| rdeg5 | 7.08 | 16.69 |  |
| rdeg7 | 9.09 | 16.69 |  |
| rdeg9 | 11.09 | 16.69 |  |
| ibias | 0.25 | 17.97 | moved |
| trim | 0.25 | 19.47 | moved |

**E edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| o2 | 69.34 | 34.12 |  |

## xdac (r2r)

- Size: 71.75 × 54.12 (GDS)
- Placement: x 185.00, y 91.00, R90 (rot 90, mirror false)
- Pins moved: 9

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| out | 11.05 | 53.87 | moved |

**S edge** (faces east in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| b0 | 5.62 | 0.25 | moved |
| VGND | 13.12 | 0.50 |  |
| b | 17.12 | 2.50 |  |
| b1 | 20.62 | 0.25 | moved |
| c | 24.62 | 2.50 |  |
| b2 | 28.12 | 0.25 | moved |
| d | 32.12 | 2.50 |  |
| b3 | 35.62 | 0.25 | moved |
| e | 39.62 | 2.50 |  |
| b4 | 43.12 | 0.25 | moved |
| f | 47.12 | 2.50 |  |
| b5 | 50.62 | 0.25 | moved |
| g | 54.62 | 2.50 |  |
| b6 | 58.12 | 0.25 | moved |
| b7 | 65.62 | 0.25 | moved |

## xctrim (ctrim_1p)

- Size: 23.50 × 23.50 (estimate: not laid out yet)
- Placement: x 159.00, y 90.30, MX (rot 0, mirror true)
- Pins moved: 2

**S edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| n | 1.00 | 0.25 | moved |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| p | 23.25 | 11.75 | moved |

## xdbg (dbg_tg)

- Size: 5.70 × 16.30 (GDS)
- Placement: x 57.50, y 124.00, R0 (rot 0, mirror false)
- Pins moved: 3

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 2.83 | 15.30 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 2.83 | 1.00 |  |
| a | 3.70 | 0.25 | moved |
| b | 4.70 | 0.25 | moved |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| enb | 2.74 | 7.15 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| en | 5.45 | 6.35 | moved |

## xtx.xring (tx_ring)

- Size: 18.32 × 6.96 (GDS)
- Placement: x 17.50, y 140.50, MXR90 (rot 90, mirror true)
- Pins moved: none

**N edge** (faces east in the tile; left → right, x):

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

**S edge** (faces west in the tile; left → right, x):

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

**W edge** (faces south in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| out | 0.44 | 1.56 |  |
| r1 | 1.34 | 1.95 |  |
| en | 0.44 | 4.46 |  |

**E edge** (faces north in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| r12 | 16.98 | 1.95 |  |
| r13 | 16.52 | 5.01 |  |

## xtx.xls (tx_ls)

- Size: 14.25 × 19.00 (GDS)
- Placement: x 36.00, y 124.00, MYR90 (rot 270, mirror true)
- Pins moved: none

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 3.95 | 18.00 |  |
| VAPWR | 10.90 | 18.00 |  |

**S edge** (faces east in the tile; left → right, x):

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
- Placement: x 27.50, y 141.00, MYR90 (rot 270, mirror true)
- Pins moved: none

**N edge** (faces west in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VDD | 3.50 | 14.48 |  |
| VAPWR | 10.00 | 14.48 |  |

**S edge** (faces east in the tile; left → right, x):

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
- Placement: x 13.00, y 124.00, R270 (rot 270, mirror false)
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
- Placement: x 37.50, y 80.50, R270 (rot 270, mirror false)
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
- Placement: x 5.50, y 80.50, MYR90 (rot 270, mirror true)
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

- VGND strap: x 13.90, w 1.20 (met4, full height)
- VDPWR strap: x 9.30, w 1.20 (met4, full height)
- VAPWR strap: x 488.02, w 1.20 (met4, full height)
- VGND strap: x 489.72, w 1.20 (met4, full height)
- VDPWR strap: x 491.42, w 1.20 (met4, full height)
- VAPWR strap: x 276.50, w 1.20 (met4, full height)
- VGND strap: x 278.20, w 1.20 (met4, full height)
- VDPWR strap: x 279.90, w 1.20 (met4, full height)
- xdecd 1: x 0.00, y 7.00, 18.00 × 71.00
- xdecd 2: x 0.00, y 124.00, 10.00 × 35.00
- xdecd 3: x 213.00, y 2.00, 26.00 × 86.00
- xdecd 4: x 0.00, y 216.00, 51.00 × 6.00
- xdeca 1: x 242.00, y 2.00, 33.00 × 211.00
- xdeca 2: x 0.00, y 193.00, 239.00 × 20.00
- xdeca 3: x 0.00, y 162.00, 50.00 × 28.00
- xdeca 4: x 182.00, y 166.00, 57.00 × 24.00
- xdeca 5: x 185.00, y 91.00, 54.12 × 71.75 (MIM only, on top of r2r)
