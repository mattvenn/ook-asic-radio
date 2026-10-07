`default_nettype none
// TX code mode: one send = 3 bursts of (127 Gold chips + 64 off chips),
// one chip = 1040 clocks (chip_tick). Uses the shared LFSR pair in rd_gold.
//
// A send starts on the first chip tick where a request is pending, the
// LFSR2 precompute is done and TX is enabled. tx_en is registered (one clock
// after the chip boundary) so the ring-oscillator enable is glitch-free.
module rd_tx (
    input  wire       clk,
    input  wire       rst,
    input  wire       enable,     // role = TX and code mode
    input  wire       chip_tick,
    input  wire       send_req,   // pulse: request a send (also set by reset)
    input  wire       ready,      // rd_gold precompute done
    input  wire       tmpl,       // current Gold chip
    output wire       gold_load,
    output wire       gold_step,
    output reg        busy,
    output reg  [1:0] burst,      // burst number 0..2 while busy
    output reg        tx_en
);
    localparam [7:0] PERIOD = 8'd191;   // 127 + 64

    reg       pending;
    reg [7:0] idx;                       // chip index within the burst period

    wire start    = chip_tick & ~busy & pending & ready & enable;
    wire last     = (idx == PERIOD - 8'd1);
    assign gold_load = start | (chip_tick & busy & last);
    assign gold_step = chip_tick & busy & ~last;

    always @(posedge clk) begin
        if (rst) begin
            pending <= 1'b1;
            busy    <= 1'b0;
            burst   <= 2'd0;
            idx     <= 8'd0;
            tx_en   <= 1'b0;
        end else begin
            if (send_req) pending <= 1'b1;
            if (start) begin
                pending <= send_req;
                busy    <= 1'b1;
                burst   <= 2'd0;
                idx     <= 8'd0;
            end else if (chip_tick && busy) begin
                if (last) begin
                    idx <= 8'd0;
                    if (burst == 2'd2)
                        busy <= 1'b0;
                    else
                        burst <= burst + 2'd1;
                end else begin
                    idx <= idx + 8'd1;
                end
            end
            // chip value for the chip that is now current
            tx_en <= busy & enable & (idx < 8'd127) & tmpl;
        end
    end
endmodule
