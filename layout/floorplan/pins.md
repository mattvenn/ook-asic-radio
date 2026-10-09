# Floorplan: block positions and pin positions

Generated from the floorplan page's variant **Matt layout 3 (Claude)** by `layout/floorplan/page/pinreport.js`; the placements are also in `floorplan.json` next to this file.

- Coordinates in µm. **Placement**: lower-left of the placed (transformed) bbox in the tile, and the GDS orientation (KLayout `DCplxTrans(1, rot, mirror, …)`, mirror about x first).
- **Pins**: in each block's *own* frame (its bbox lower-left = 0, 0, before the orientation), grouped by the block's own edge. "moved" = a new position for the re-layout / re-harden; the others are where the GDS has them now. The tile direction each edge faces after placement is given in brackets.
- Moved pins sit on the edge facing what they connect to (`pinfit.js`). Positions along an edge are targets: pins closer than ~1 µm were spread to 1 µm.

## Checks (with the moved pins)

| rule | status | value |
|---|---|---|
| 1. Chain input far from the macro | warn | 60 µm |
| 2. Late stages away from the input | pass | 60 µm |
| 3. Clock edges off the RX | pass | 70 µm |
| 4. Short analog path | warn | 377 µm |
| 5. TX at ua[3] / ua[4] | pass | 36 µm |
| 6. Bias next to the chain | pass | 3 µm |
| 7. Decap VAPWR | fail | 61 % |
| 7. Decap VDPWR | pass | 103 % |
| 8. TX away from the RX input | warn | 14 µm |
| 9. Overlaps and spacing | pass | none |
| 9. TT pin channel clear | pass | 12.6 µm |
| P. Power straps | pass | 5 clear |

## macro (radio_digital)

- Size: 450.50 × 109.66 (reshaped from 260 × 190, same area: re-harden at this size)
- Placement: x 19.50, y 103.50, MY (rot 180, mirror true)
- Pins moved: 57

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| clk | 339.86 | 109.41 | moved |
| rst_n | 342.62 | 109.41 | moved |
| ui_in[0] | 345.38 | 109.41 | moved |
| ui_in[1] | 348.14 | 109.41 | moved |
| ui_in[2] | 350.90 | 109.41 | moved |
| ui_in[3] | 353.66 | 109.41 | moved |
| ui_in[4] | 356.42 | 109.41 | moved |
| ui_in[5] | 359.18 | 109.41 | moved |
| ui_in[6] | 361.94 | 109.41 | moved |
| ui_in[7] | 364.70 | 109.41 | moved |
| uio_in[0] | 367.46 | 109.41 | moved |
| uio_in[1] | 370.22 | 109.41 | moved |
| uio_in[2] | 372.98 | 109.41 | moved |
| uio_in[3] | 375.74 | 109.41 | moved |
| uio_in[4] | 378.50 | 109.41 | moved |
| uio_in[5] | 381.26 | 109.41 | moved |
| uio_in[6] | 384.02 | 109.41 | moved |
| uio_in[7] | 386.78 | 109.41 | moved |
| uo_out[0] | 389.54 | 109.41 | moved |
| uo_out[1] | 392.30 | 109.41 | moved |
| uo_out[2] | 395.06 | 109.41 | moved |
| uo_out[3] | 397.82 | 109.41 | moved |
| uo_out[4] | 400.58 | 109.41 | moved |
| uo_out[5] | 403.34 | 109.41 | moved |
| uo_out[6] | 406.10 | 109.41 | moved |
| uo_out[7] | 408.86 | 109.41 | moved |
| uio_out[0] | 411.62 | 109.41 | moved |
| uio_out[1] | 414.38 | 109.41 | moved |
| uio_out[2] | 417.14 | 109.41 | moved |
| uio_out[3] | 419.90 | 109.41 | moved |
| uio_out[4] | 422.66 | 109.41 | moved |
| uio_out[5] | 425.42 | 109.41 | moved |
| uio_out[6] | 428.18 | 109.41 | moved |
| uio_out[7] | 430.94 | 109.41 | moved |
| uio_oe[0] | 433.70 | 109.41 | moved |
| uio_oe[1] | 436.46 | 109.41 | moved |
| uio_oe[2] | 439.22 | 109.41 | moved |
| uio_oe[3] | 441.98 | 109.41 | moved |
| uio_oe[4] | 444.74 | 109.41 | moved |
| uio_oe[5] | 447.50 | 109.41 | moved |
| uio_oe[6] | 448.50 | 109.41 | moved |
| uio_oe[7] | 449.50 | 109.41 | moved |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| trim_out[7] | 1.00 | 0.25 | moved |
| trim_out[6] | 2.00 | 0.25 | moved |
| trim_out[5] | 3.00 | 0.25 | moved |
| trim_out[4] | 5.75 | 0.25 | moved |
| trim_out[3] | 13.25 | 0.25 | moved |
| trim_out[2] | 20.75 | 0.25 | moved |
| trim_out[1] | 28.25 | 0.25 | moved |
| sc_phi2 | 39.74 | 0.25 | moved |
| sc_phi1 | 41.39 | 0.25 | moved |
| trim_out[0] | 43.25 | 0.25 | moved |
| comp_in | 52.37 | 0.25 | moved |
| rx_en | 381.45 | 0.25 | moved |
| dbg_en | 389.00 | 0.25 | moved |
| tx_en | 415.25 | 0.25 | moved |
| tx_en_n | 436.07 | 0.25 | moved |

## xchain (lna_chain)

- Size: 268.12 × 35.26 (GDS)
- Placement: x 90.50, y 3.00, MX (rot 0, mirror true)
- Pins moved: 2

**N edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| inp | 3.60 | 35.01 |  |
| inn | 36.76 | 35.01 |  |
| o1n | 106.42 | 18.31 |  |
| o2n | 138.96 | 18.31 |  |
| o3n | 171.50 | 18.31 |  |
| o4n | 204.04 | 18.31 |  |
| o5n | 236.58 | 18.31 |  |

**S edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| ibias | 1.00 | 0.25 | moved |
| vcm | 2.00 | 0.25 | moved |
| o1p | 106.42 | 17.61 |  |
| o2p | 138.96 | 17.61 |  |
| o3p | 171.50 | 17.61 |  |
| o4p | 204.04 | 17.61 |  |
| o5p | 236.58 | 17.61 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VSS | 0.50 | 0.75 |  |
| g1n | 7.04 | 25.75 |  |
| g1p | 6.04 | 25.75 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| outp | 267.82 | 17.61 |  |
| outn | 267.82 | 19.01 |  |
| VDD | 267.62 | 20.46 |  |

## xbias (bias_gen)

- Size: 80.22 × 49.07 (GDS)
- Placement: x 86.50, y 41.00, R0 (rot 0, mirror false)
- Pins moved: 5

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| en | 2.05 | 48.82 | moved |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| ib_chain | 5.00 | 0.25 | moved |
| vcm | 6.00 | 0.25 | moved |
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

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| enb | 6.51 | 11.25 |  |
| ota | 2.05 | 12.05 |  |
| pr | 2.05 | 15.25 |  |
| VDD | 15.18 | 23.05 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| ib_det | 79.97 | 13.30 | moved |
| ib_comp | 79.97 | 43.42 | moved |

## xdet (log_det)

- Size: 87.33 × 31.01 (GDS)
- Placement: x 255.35, y 41.00, MX (rot 0, mirror true)
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
| ibias_det | 0.25 | 17.71 | moved |
| t1p | 1.70 | 23.02 |  |
| det | 0.25 | 30.01 | moved |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VDD | 86.73 | 15.51 |  |

## xlpf (lpf_rc)

- Size: 65.20 × 35.02 (GDS)
- Placement: x 170.00, y 42.50, R0 (rot 0, mirror false)
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
| in | 64.95 | 1.00 | moved |
| out | 64.95 | 2.00 | moved |

## xavg (avg_sc)

- Size: 77.35 × 30.40 (GDS)
- Placement: x 361.12, y 0.50, R0 (rot 0, mirror false)
- Pins moved: 4

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| out | 1.00 | 30.15 | moved |
| phi1 | 67.49 | 30.15 | moved |
| phi1b | 67.71 | 24.75 |  |
| VDD | 68.52 | 29.65 |  |
| phi2b | 68.91 | 25.55 |  |
| phi2 | 69.14 | 30.15 | moved |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| in | 0.25 | 29.40 | moved |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| VSS | 68.52 | 15.55 |  |
| cs | 70.06 | 21.55 |  |

## xcomp (comp_ct)

- Size: 73.45 × 41.97 (GDS)
- Placement: x 345.18, y 54.30, R0 (rot 0, mirror false)
- Pins moved: 5

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| d1 | 18.65 | 33.31 |  |
| tail | 27.30 | 29.32 |  |
| vref | 28.60 | 31.71 |  |
| d2 | 36.90 | 30.92 |  |
| VDD | 37.00 | 41.22 |  |
| sa | 40.30 | 32.52 |  |
| sb | 44.45 | 28.52 |  |
| out | 72.45 | 41.72 | moved |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| rdeg4 | 6.08 | 5.61 |  |
| rdeg6 | 8.09 | 5.61 |  |
| rdeg8 | 10.09 | 5.61 |  |
| rdeg10 | 12.09 | 5.61 |  |
| rdeg12 | 14.09 | 5.61 |  |
| rdeg14 | 16.09 | 5.61 |  |
| inn | 16.94 | 0.25 | moved |
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
| trim | 72.45 | 0.25 | moved |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| inp | 0.25 | 1.00 | moved |
| rdeg2 | 4.08 | 5.61 |  |
| rdeg1 | 3.08 | 16.69 |  |
| rdeg11 | 13.09 | 16.69 |  |
| rdeg13 | 15.09 | 16.69 |  |
| rdeg3 | 5.08 | 16.69 |  |
| rdeg5 | 7.08 | 16.69 |  |
| rdeg7 | 9.09 | 16.69 |  |
| rdeg9 | 11.09 | 16.69 |  |
| ibias | 0.25 | 30.12 | moved |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| o2 | 69.34 | 34.12 |  |

## xdac (r2r)

- Size: 71.75 × 54.12 (GDS)
- Placement: x 421.13, y 44.33, MX (rot 0, mirror true)
- Pins moved: 9

**N edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| out | 20.87 | 53.87 | moved |

**S edge** (faces north in the tile; left → right, x):

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
| b5 | 47.87 | 0.25 | moved |
| b6 | 48.87 | 0.25 | moved |
| b7 | 49.87 | 0.25 | moved |
| g | 54.62 | 2.50 |  |

## xctrim (ctrim_1p)

- Size: 23.50 × 23.50 (estimate: not laid out yet)
- Placement: x 441.00, y 4.50, MX (rot 0, mirror true)
- Pins moved: 2

**S edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| n | 1.00 | 0.25 | moved |
| p | 2.00 | 0.25 | moved |

## xdbg (dbg_tg)

- Size: 5.70 × 16.30 (GDS)
- Placement: x 80.00, y 3.00, R0 (rot 0, mirror false)
- Pins moved: 3

**N edge** (faces north in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| en | 1.00 | 16.05 | moved |
| VDD | 2.83 | 15.30 |  |

**S edge** (faces south in the tile; left → right, x):

| pin | x | y | |
|---|---|---|---|
| VSS | 2.83 | 1.00 |  |

**W edge** (faces west in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| enb | 2.74 | 7.15 |  |

**E edge** (faces east in the tile; bottom → top, y):

| pin | x | y | |
|---|---|---|---|
| b | 5.45 | 1.00 | moved |
| a | 5.45 | 15.30 | moved |

## xtx.xring (tx_ring)

- Size: 18.32 × 6.96 (GDS)
- Placement: x 58.00, y 68.00, MXR90 (rot 90, mirror true)
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
- Placement: x 51.50, y 51.00, MYR90 (rot 270, mirror true)
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
- Placement: x 40.00, y 68.00, MYR90 (rot 270, mirror true)
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
- Placement: x 25.50, y 51.00, R270 (rot 270, mirror false)
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
- Placement: x 50.00, y 7.50, R270 (rot 270, mirror false)
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
- Placement: x 18.00, y 7.50, MYR90 (rot 270, mirror true)
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
- xdeca 1: x 362.00, y 34.00, 56.00 × 17.00
- xdeca 2: x 40.00, y 89.00, 30.00 × 9.00
- xdeca 3: x 17.00, y 67.00, 20.00 × 31.00
- xdeca 4: x 421.00, y 34.00, 43.00 × 7.00
- xdeca 5: x 0.00, y 2.00, 14.00 × 222.00
- xdeca 6: x 467.00, y 2.00, 26.00 × 39.00
- xdeca 7: x 475.00, y 101.00, 18.00 × 123.00
- xdeca 8: x 422.13, y 45.33, 65.29 × 52.12 (MIM only, on top of r2r)
- xdecd 1: x 238.00, y 41.00, 14.00 × 37.00
- xdecd 2: x 170.00, y 81.00, 172.00 × 17.00
- xdecd 3: x 346.00, y 41.00, 13.00 × 10.00
- xdecd 4: x 80.00, y 22.00, 8.00 × 16.00
- xdecd 5: x 73.00, y 51.00, 11.00 × 47.00
