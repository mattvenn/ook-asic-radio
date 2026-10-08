`default_nettype none
// Integrated clock gate: gclk = clk while en is high, low otherwise.
// Latch-based (the latch is transparent while clk is low), so en may change
// any time while clk is high without glitching gclk; en must be settled
// before the rising edge of clk, like a flop's D.
//
// Silicon: sky130_fd_sc_hd__dlclkp (used on TT08 #770 "Sequential Shadows",
// reported working). In simulation (SIM defined: RTL cocotb, lint) a
// behavioural model of the same cell.
module rd_cg (
    input  wire clk,
    input  wire en,
    output wire gclk
);
`ifdef SIM
    reg en_l;
    /* verilator lint_off LATCH */
    always @(clk or en)
        if (!clk) en_l = en;
    /* verilator lint_on LATCH */
    assign gclk = clk & en_l;
`else
    sky130_fd_sc_hd__dlclkp_1 u_cg (.CLK(clk), .GATE(en), .GCLK(gclk));
`endif
endmodule
