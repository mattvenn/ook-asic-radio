// The clock gate as a black box on both sides: it is the same library cell,
// instantiated by name in the RTL (rd_cg.v), so eqy matches it by instance name
// and proves its inputs (CLK, GATE) equivalent instead of reasoning through its latch.
(* blackbox *)
module sky130_fd_sc_hd__dlclkp_1 (output GCLK, input GATE, input CLK);
endmodule
