`default_nettype none
`timescale 1ns / 1ps

// TT-style testbench: the user project on the TT pins only (see test.py).
module tb ();
    reg        clk;
    reg        rst_n;
    reg        ena;
    reg  [7:0] ui_in;
    reg  [7:0] uio_in;
    wire [7:0] uo_out;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;
    wire [7:0] ua;

    tt_um_mattvenn_radio user_project (
        .ui_in  (ui_in),
        .uo_out (uo_out),
        .uio_in (uio_in),
        .uio_out(uio_out),
        .uio_oe (uio_oe),
        .ua     (ua),
        .ena    (ena),
        .clk    (clk),
        .rst_n  (rst_n)
    );
endmodule
