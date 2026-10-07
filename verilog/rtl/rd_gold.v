`default_nettype none
// Gold-127 code generator shared by the RX correlator and the TX.
//
// Two 7-bit Fibonacci LFSRs (model/gold.py). State convention matches the
// integers in test/vectors/tx_codes.npz: bit 6 = stage 1 (where feedback
// enters), bit 0 = stage 7 = output.
//   LFSR1 taps (7,3)       : fb = s[0] ^ s[4]
//   LFSR2 taps (7,3,2,1)   : fb = s[0] ^ s[4] ^ s[5] ^ s[6]
// Code k (0..126) = M1 xor (M2 advanced k chips); code 127 = M1 alone.
//
// When a new code is adopted (load_code), LFSR2's start state is precomputed
// by stepping a copy of it `code` times (<= 127 clocks). `ready` is low while
// that runs. The runtime pair is loaded with (SEED, l2_start) by `load` and
// advanced by `step`; `chip` is the current template chip.
module rd_gold (
    input  wire       clk,
    input  wire       rst,
    input  wire [6:0] code_in,
    input  wire       load_code,
    input  wire       load,
    input  wire       step,
    output wire       chip,
    output wire       ready,
    output wire [6:0] code
);
    localparam [6:0] SEED = 7'h7f;

    function [6:0] step1(input [6:0] s);
        step1 = {s[0] ^ s[4], s[6:1]};
    endfunction
    function [6:0] step2(input [6:0] s);
        step2 = {s[0] ^ s[4] ^ s[5] ^ s[6], s[6:1]};
    endfunction

    reg [6:0] code_q;
    reg [6:0] pre_cnt;
    reg [6:0] l2_start;
    reg [6:0] l1, l2;

    always @(posedge clk) begin
        if (rst || load_code) begin
            code_q   <= code_in;
            pre_cnt  <= code_in;
            l2_start <= SEED;
        end else if (pre_cnt != 7'd0) begin
            l2_start <= step2(l2_start);
            pre_cnt  <= pre_cnt - 7'd1;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            l1 <= SEED;
            l2 <= SEED;
        end else if (load) begin
            l1 <= SEED;
            l2 <= l2_start;
        end else if (step) begin
            l1 <= step1(l1);
            l2 <= step2(l2);
        end
    end

    assign chip  = l1[0] ^ (l2[0] & ~(&code_q));
    assign ready = (pre_cnt == 7'd0);
    assign code  = code_q;
endmodule
