`default_nettype none
// RX control: comparator trim servo, detection events, 2-of-3 pairing,
// holdoff and the LED (model/radio.py RxDigital, test/vectors/README.md).
//
// No absolute chip counter is kept. Every time in the model is replaced by
// an age in chips (incremented on the chip tick = the tick with k == 0):
//   * an event opens at chip count t (age 0) and closes on the first chip
//     tick where the count reaches t + 8, i.e. exactly when its age hits 8;
//     the close is evaluated the clock after that chip tick (chip_d);
//   * at that close, the age of a history entry prev is (t + 8) - prev, so
//     the model's d = t - prev = age - 8: d = 191+/-2 -> age 197..201,
//     d = 382+/-2 -> age 388..392. History ages saturate at 511 (>392 can
//     never match again), which also makes them wrap-free.
//   * holdoff: the model's holdoff_end = t_toggle + 9615, tested as
//     t >= holdoff_end. With hold_age = chips since the toggling close,
//     t - t_toggle = hold_age, so the test is hold_age >= 9615 (saturating;
//     reset value 9615 = no holdoff).
// Scores arrive from rd_corr 128 clocks after the window-end tick, before
// the next tick, so the chip count of an opening event is the current one
// (age 0) and score results and closes are never simultaneous.
module rd_rx (
    input  wire       clk,
    input  wire       rst,
    input  wire       tick,       // sample tick (RX enabled)
    input  wire       chip_tick,  // tick with k == 0 (RX enabled)
    input  wire       c,          // comparator sample
    input  wire       done,       // score valid (from rd_corr)
    input  wire [6:0] score,
    output reg  [7:0] trim,
    output reg        dir,        // last servo step: 1 = up
    output reg        ev_open,
    output reg        ev_close,   // 1-clock pulse when an event closes
    output reg  [6:0] ev_score,   // max score of the open/last event
    output reg        led,
    output reg        toggle,     // 1-clock pulse on an LED toggle
    output reg        recent      // an event closed within the last ~1.7 s
);
    localparam [6:0]  THRESH  = 7'd97;
    localparam [13:0] HOLDOFF = 14'd9615;

    reg        chip_d;
    reg [3:0]  ev_age;
    reg [8:0]  h0_age, h1_age;    // h0 = newest history entry
    reg        h0_v, h1_v;
    reg [13:0] hold_age;
    reg [13:0] disp_age;

    function pair_ok(input [8:0] a);
        pair_ok = (a >= 9'd197 && a <= 9'd201) || (a >= 9'd388 && a <= 9'd392);
    endfunction

    wire closing = chip_d & ev_open & (ev_age == 4'd8);
    wire free    = (hold_age >= HOLDOFF);
    wire paired  = free & ((h0_v & pair_ok(h0_age)) | (h1_v & pair_ok(h1_age)));

    // trim servo
    always @(posedge clk) begin
        if (rst) begin
            trim <= 8'd128;
            dir  <= 1'b0;
        end else if (tick) begin
            dir <= c;
            if (c && trim != 8'hff)
                trim <= trim + 8'd1;
            else if (!c && trim != 8'h00)
                trim <= trim - 8'd1;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            chip_d   <= 1'b0;
            ev_open  <= 1'b0;
            ev_age   <= 4'd0;
            ev_score <= 7'd0;
            ev_close <= 1'b0;
            h0_age   <= 9'd0;
            h1_age   <= 9'd0;
            h0_v     <= 1'b0;
            h1_v     <= 1'b0;
            hold_age <= HOLDOFF;
            led      <= 1'b0;
            toggle   <= 1'b0;
            disp_age <= 14'h3fff;
            recent   <= 1'b0;
        end else begin
            chip_d   <= chip_tick;
            ev_close <= 1'b0;
            toggle   <= 1'b0;
            recent   <= ~(&disp_age);

            // ages advance on the chip tick
            if (chip_tick) begin
                if (ev_open)        ev_age   <= ev_age + 4'd1;
                if (!(&h0_age))     h0_age   <= h0_age + 9'd1;
                if (!(&h1_age))     h1_age   <= h1_age + 9'd1;
                if (hold_age != HOLDOFF) hold_age <= hold_age + 14'd1;
                if (!(&disp_age))   disp_age <= disp_age + 14'd1;
            end

            // score from the correlator
            if (done && score >= THRESH) begin
                if (!ev_open) begin
                    ev_open  <= 1'b1;
                    ev_age   <= 4'd0;
                    ev_score <= score;
                end else if (score > ev_score) begin
                    ev_score <= score;
                end
            end

            // event close + pairing
            if (closing) begin
                ev_open  <= 1'b0;
                ev_close <= 1'b1;
                disp_age <= 14'd0;
                if (paired) begin
                    led      <= ~led;
                    toggle   <= 1'b1;
                    hold_age <= 14'd0;
                    h0_v     <= 1'b0;
                    h1_v     <= 1'b0;
                end else begin
                    h1_age <= h0_age;
                    h1_v   <= h0_v;
                    h0_age <= 9'd8;
                    h0_v   <= 1'b1;
                end
            end
        end
    end
endmodule
