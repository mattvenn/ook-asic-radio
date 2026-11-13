// Stand-ins for the sky130_fd_sc_hd UDPs (primitives.v), which Yosys can't read.
// Only the ones the functional (no power pins) models of the cells in
// radio_digital.nl.v use, written from the UDP tables (0/1 values only).
module \sky130_fd_sc_hd__udp_dff$P (output reg Q, input D, input CLK);
    always @(posedge CLK) Q <= D;
endmodule

module \sky130_fd_sc_hd__udp_dlatch$P (output reg Q, input D, input GATE);
    always @* if (GATE) Q = D;
endmodule

module sky130_fd_sc_hd__udp_mux_2to1 (output X, input A0, input A1, input S);
    assign X = S ? A1 : A0;
endmodule

// conb_1 (tie cell) uses the pullup / pulldown gate primitives
module \pullup (output Y);
    assign Y = 1'b1;
endmodule

module \pulldown (output Y);
    assign Y = 1'b0;
endmodule
