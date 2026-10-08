`default_nettype none
// RX chip slicer + 4 x 127-bit chip registers + one shared sequential
// XNOR-popcount engine (model/radio.py RxDigital.step/_shift).
//
// Phases p = 0,2,4,6 (index q = p/2). Phase p's 8-sample window ends on the
// tick where k == (p+7) mod 8, i.e. on odd k, with q = (k[2:1] + 1) mod 4.
// Majority: chip bit = count > 4 or (count == 4 and last sample == 1). The
// 3-bit counter holds the first 7 samples of the window, so with c = last
// sample: bit = (cnt >= 5) | (c & cnt >= 3).
//
// On a window-end tick the bit shifts into sr[q] (bit 0 = newest) and the
// popcount starts: for j = 0..126 (one per clock) sr[q][126] (= chip j of a
// fully-arrived burst) is compared with template chip j and sr[q] is rotated
// by one, so after 127 clocks the register is back where it was. `done`
// pulses with `score` 128 clocks after the tick, i.e. before the next tick
// (130 clocks), so the score is still tagged with the tick's chip count.
module rd_corr (
    input  wire       clk,
    input  wire       rst,
    input  wire       tick,       // sample tick (RX enabled)
    input  wire [2:0] k,          // sample index mod 8 of this tick
    input  wire       c,          // comparator sample
    input  wire       tmpl,       // template chip from rd_gold
    output wire       gold_load,
    output wire       gold_step,
    output reg        done,
    output reg  [6:0] score
);
    reg [126:0] sr0, sr1, sr2, sr3;
    reg [2:0]   cnt0, cnt1, cnt2, cnt3;
    reg         busy;
    reg [6:0]   j;
    reg [1:0]   sel;
    reg [6:0]   acc;

    wire       wend  = tick & k[0];
    wire [1:0] qend  = k[2:1] + 2'd1;

    // majority decision for the phase whose window ends now
    reg [2:0] cnt_end;
    always @(*) begin
        case (qend)
            2'd0: cnt_end = cnt0;
            2'd1: cnt_end = cnt1;
            2'd2: cnt_end = cnt2;
            default: cnt_end = cnt3;
        endcase
    end
    wire bit_new = (cnt_end >= 3'd5) | (c & (cnt_end >= 3'd3));

    // per-phase sample counters
    always @(posedge clk) begin
        if (rst) begin
            cnt0 <= 3'd0; cnt1 <= 3'd0; cnt2 <= 3'd0; cnt3 <= 3'd0;
        end else if (tick) begin
            cnt0 <= (wend && qend == 2'd0) ? 3'd0 : cnt0 + {2'd0, c};
            cnt1 <= (wend && qend == 2'd1) ? 3'd0 : cnt1 + {2'd0, c};
            cnt2 <= (wend && qend == 2'd2) ? 3'd0 : cnt2 + {2'd0, c};
            cnt3 <= (wend && qend == 2'd3) ? 3'd0 : cnt3 + {2'd0, c};
        end
    end

    // oldest bit of the register being correlated
    reg msb;
    always @(*) begin
        case (sel)
            2'd0: msb = sr0[126];
            2'd1: msb = sr1[126];
            2'd2: msb = sr2[126];
            default: msb = sr3[126];
        endcase
    end

    // shift (new chip) or rotate (correlation); both move towards bit 126
    // After reset `clr` shifts zeros into all four registers for 127 clocks
    // (the model starts with empty registers); cheaper than 508 reset muxes.
    // It finishes before the first window-end tick (k = 1, ~260 clocks).
    reg  clr;
    wire din = clr ? 1'b0 : busy ? msb : bit_new;
    wire en0 = clr | (busy ? (sel == 2'd0) : (wend && qend == 2'd0));
    wire en1 = clr | (busy ? (sel == 2'd1) : (wend && qend == 2'd1));
    wire en2 = clr | (busy ? (sel == 2'd2) : (wend && qend == 2'd2));
    wire en3 = clr | (busy ? (sel == 2'd3) : (wend && qend == 2'd3));

    // chip registers (no reset: see clr). Each register is clocked only
    // when it shifts or rotates: an integrated clock gate per register
    // (rd_cg) replaces 127 enable muxes per register. Each register is idle
    // most of the time (one shift per 8 samples, a 127-clock rotation every
    // 4th window end).
    wire gclk0, gclk1, gclk2, gclk3;
    rd_cg u_cg0 (.clk(clk), .en(en0), .gclk(gclk0));
    rd_cg u_cg1 (.clk(clk), .en(en1), .gclk(gclk1));
    rd_cg u_cg2 (.clk(clk), .en(en2), .gclk(gclk2));
    rd_cg u_cg3 (.clk(clk), .en(en3), .gclk(gclk3));
    always @(posedge gclk0) sr0 <= {sr0[125:0], din};
    always @(posedge gclk1) sr1 <= {sr1[125:0], din};
    always @(posedge gclk2) sr2 <= {sr2[125:0], din};
    always @(posedge gclk3) sr3 <= {sr3[125:0], din};

    wire match = ~(msb ^ tmpl);

    always @(posedge clk) begin
        if (rst) begin
            clr   <= 1'b1;
            busy  <= 1'b0;
            j     <= 7'd0;
            sel   <= 2'd0;
            acc   <= 7'd0;
            done  <= 1'b0;
            score <= 7'd0;
        end else begin
            done <= 1'b0;
            if (clr) begin
                j <= j + 7'd1;
                if (j == 7'd126) begin
                    clr <= 1'b0;
                    j   <= 7'd0;
                end
            end else if (busy) begin
                acc <= acc + {6'd0, match};
                j   <= j + 7'd1;
                if (j == 7'd126) begin
                    busy  <= 1'b0;
                    done  <= 1'b1;
                    score <= acc + {6'd0, match};
                end
            end else if (wend) begin
                busy <= 1'b1;
                j    <= 7'd0;
                acc  <= 7'd0;
                sel  <= qend;
            end
        end
    end

    assign gold_load = wend & ~busy;
    assign gold_step = busy;
endmodule
