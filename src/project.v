/*
 * Copyright (c) 2026 Matt Venn
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// LVS stub for the analog top level (see mag/README.md): this is treated as a
// blackbox gate-level netlist, so the instance and net names here must match
// the layout. Instances are added as the blocks are laid out:
//   radio_digital  - hardened digital macro (openlane/radio_digital)
//   TX: ring oscillator + antiphase drivers -> ua[3], ua[4]
//   RX: differential LNA/limiter, log detector, LPF, switched-cap average,
//       comparator, R2R trim DAC + attenuator; ua[0], ua[1] in, ua[2] debug
module tt_um_mattvenn_radio (
    input  wire       VGND,
    input  wire       VDPWR,    // 1.8v power supply
    input  wire       VAPWR,    // 3.3v power supply (reserved for a possible 3.3 V TX driver)
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    inout  wire [7:0] ua,       // Analog pins, only ua[5:0] can be used
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

endmodule
