`default_nettype none
// radio_digital: digital macro of the 433 MHz OOK radio (code mode + raw
// pass-throughs). Hardened separately and instantiated in the analog top.
//
// Clock 10 MHz. Synchronous active-high reset internally (rst_n registered).
//
// Pins
//   ui_in[6:0]  code (DIP switches; synchronised, 50 ms debounce)
//   ui_in[7]    role, latched at reset release: 1 = TX, 0 = RX
//   uio_in[1:0] mode strap, latched at reset release ONLY if
//               uio_in[7:4] == 4'b1010 (magic), else code mode:
//                 00 code (default)   01 raw TX (tx_en = uio_in[2])
//                 10 data (reserved; behaves as code mode for now)
//                 11 reserved (code mode)
//   uio_in[2]   at reset release, with the same magic: 1 = analog debug,
//               dbg_en = 1 connects the detector output (det) to ua[4]
//               through a transmission gate. Default: off (det isolated).
//   uio_in[3]   single-ended TX strap, latched at reset release ONLY with
//               the same magic: 1 = drive ua[0] only (monopole fallback;
//               tx_en_n stays 0). Default (no magic / floating): both arms.
//               uio_oe is 0 during reset so the RP2350 can drive the strap
//               on uio[7:4]; it must release those pins right after reset.
//   uio_in[2]   raw TX key (mode 01): drives tx_en combinationally
//   uio_out[3]  raw RX: synchronised comparator bit (all modes)
//   uio_out[4]  RX event open (a burst is being detected, ~8 chips)
//   uio_out[5]  RX LED toggle pulse (one clock)
//   uio_out[6]  RX trim servo direction (last comparator sample)
//   uio_out[7]  TX sending (3-burst send in progress)
//   uio_oe      8'b1111_1000 after reset, 0 during reset
//   uo_out      7-seg {dp,g,f,e,d,c,b,a}
//                 RX: digit 0..9 = link quality from the last event score
//                     (97..127), '-' when no event in the last ~1.7 s;
//                     dp = LED toggle state
//                 TX: '1'..'3' = burst being sent, 't' when idle; dp = tx_en
//                 raw mode: 'r'; dp = tx_en (TX) / comparator bit (RX)
//   comp_in     comparator output (asynchronous; 2-flop synchroniser)
//   trim_out    8-bit trim DAC code (servo)
//   tx_en       ring oscillator enable; also the out_p arm enable (tx_top en_p)
//   tx_en_n     out_n arm enable (tx_top en_n) = tx_en unless single-ended.
//               A disabled arm is parked low.
//   rx_en       RX analog power enable (role = RX)
//   dbg_en      det -> ua[4] transmission gate enable (debug strap)
//   sc_phi1/2   non-overlapping switched-cap clocks, one cycle per sample
//
// Timing vs test/vectors/README.md: sample i is processed at the clock edge
// 130*(i+1)+1 after the first clock edge with rst_n high (one clock for the
// rst_n register, the first tick when the divider reaches 129). Because of
// the synchroniser the value used is comp_in as it was 2 clocks before that
// edge, so comp_in must be stable for >= 3 clocks before each tick.
module radio_digital (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] ui_in,
    input  wire [7:0] uio_in,
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       comp_in,
    output wire [7:0] trim_out,
    output wire       tx_en,
    output wire       tx_en_n,
    output wire       rx_en,
    output wire       dbg_en,
    output reg        sc_phi1,
    output reg        sc_phi2
);
    localparam [1:0] M_CODE = 2'b00, M_RAW = 2'b01;

    // ---------------------------------------------------------------- reset, straps
    reg       rst;
    reg       role_tx;
    reg [1:0] mode;
    reg       oe;
    reg       se;
    reg       dbg;
    always @(posedge clk) begin
        rst <= ~rst_n;
        if (rst) begin
            role_tx <= ui_in[7];
            mode    <= (uio_in[7:4] == 4'b1010) ? uio_in[1:0] : M_CODE;
            se      <= (uio_in[7:4] == 4'b1010) & uio_in[3];
            dbg     <= (uio_in[7:4] == 4'b1010) & uio_in[2];
            oe      <= 1'b0;
        end else begin
            oe      <= 1'b1;
        end
    end
    wire raw = (mode == M_RAW);
    assign dbg_en = dbg;

    // ---------------------------------------------------------------- synchronisers
    reg       comp_s1, comp_s2;
    reg [6:0] code_s1, code_s2;
    always @(posedge clk) begin
        comp_s1 <= comp_in;
        comp_s2 <= comp_s1;
        code_s1 <= ui_in[6:0];
        code_s2 <= code_s1;
    end

    // ---------------------------------------------------------------- timing
    // div 0..129: tick every 130 clocks; k = sample index mod 8
    reg [7:0] div;
    reg [2:0] k;
    wire tick      = (div == 8'd129);
    wire chip_tick = tick & (k == 3'd0);
    always @(posedge clk) begin
        if (rst) begin
            div <= 8'd0;
            k   <= 3'd0;
        end else begin
            div <= tick ? 8'd0 : div + 8'd1;
            if (tick) k <= k + 3'd1;
        end
    end

    // switched-cap phases (registered): phi1 high for 61 clocks, 4 clocks dead,
    // phi2 high for 61 clocks, 4 clocks dead (div 1..61 / 66..126)
    always @(posedge clk) begin
        if (rst) begin
            sc_phi1 <= 1'b0;
            sc_phi2 <= 1'b0;
        end else begin
            sc_phi1 <= rx_en & (div < 8'd61);
            sc_phi2 <= rx_en & (div >= 8'd65) & (div < 8'd126);
        end
    end

    // ---------------------------------------------------------------- code debounce
    // The code is adopted after it has been stable and different for 48 chips
    // (~50 ms). Not while a TX send is in progress.
    wire       tx_busy;
    wire [6:0] code;
    reg  [5:0] deb;
    wire       code_change = (deb == 6'd48) & ~tx_busy;
    always @(posedge clk) begin
        if (rst || code_s2 == code || code_s1 != code_s2)
            deb <= 6'd0;
        else if (chip_tick && deb != 6'd48)
            deb <= deb + 6'd1;
    end

    // ---------------------------------------------------------------- Gold codes
    wire tmpl, gold_ready;
    wire rx_load, rx_step, tx_load, tx_step;
    rd_gold u_gold (
        .clk(clk), .rst(rst),
        .code_in(code_s2), .load_code(code_change),
        .load(role_tx ? tx_load : rx_load),
        .step(role_tx ? tx_step : rx_step),
        .chip(tmpl), .ready(gold_ready), .code(code)
    );

    // ---------------------------------------------------------------- RX
    assign rx_en = ~role_tx;
    wire rx_tick      = tick & rx_en;
    wire rx_chip_tick = chip_tick & rx_en;
    wire       corr_done;
    wire [6:0] corr_score;
    rd_corr u_corr (
        .clk(clk), .rst(rst),
        .tick(rx_tick), .k(k), .c(comp_s2), .tmpl(tmpl),
        .gold_load(rx_load), .gold_step(rx_step),
        .done(corr_done), .score(corr_score)
    );

    wire       ev_open, ev_close, led, toggle, dir, recent;
    wire [6:0] ev_score;
    rd_rx u_rx (
        .clk(clk), .rst(rst),
        .tick(rx_tick), .chip_tick(rx_chip_tick), .c(comp_s2),
        .done(corr_done), .score(corr_score),
        .trim(trim_out), .dir(dir),
        .ev_open(ev_open), .ev_close(ev_close), .ev_score(ev_score),
        .led(led), .toggle(toggle), .recent(recent)
    );

    // ---------------------------------------------------------------- TX
    wire [1:0] burst;
    wire       tx_code_en;
    rd_tx u_tx (
        .clk(clk), .rst(rst),
        .enable(role_tx & ~raw), .chip_tick(chip_tick),
        .send_req(code_change & role_tx), .ready(gold_ready), .tmpl(tmpl),
        .gold_load(tx_load), .gold_step(tx_step),
        .busy(tx_busy), .burst(burst), .tx_en(tx_code_en)
    );
    assign tx_en   = raw ? uio_in[2] : tx_code_en;
    assign tx_en_n = tx_en & ~se;

    // ---------------------------------------------------------------- 7-segment
    // link quality digit = (score - 97) * 21 / 64  -> 97..127 maps to 0..9
    wire [4:0] q    = ev_score[4:0] - 5'd1;           // 97 = 7'b1100001
    wire [9:0] q21  = {5'd0, q} * 10'd21;
    wire [3:0] qdig = q21[9:6];

    reg [3:0] sym;
    reg       dp;
    always @(*) begin
        if (raw) begin
            sym = 4'hc;                               // 'r'
            dp  = role_tx ? tx_en : comp_s2;
        end else if (role_tx) begin
            sym = tx_busy ? {2'b00, burst} + 4'd1 : 4'hb;   // '1'..'3' / 't'
            dp  = tx_code_en;
        end else begin
            sym = recent ? qdig : 4'ha;               // digit / '-'
            dp  = led;
        end
    end

    reg [6:0] seg;
    always @(*) begin
        case (sym)            // gfedcba
            4'h0: seg = 7'b0111111;
            4'h1: seg = 7'b0000110;
            4'h2: seg = 7'b1011011;
            4'h3: seg = 7'b1001111;
            4'h4: seg = 7'b1100110;
            4'h5: seg = 7'b1101101;
            4'h6: seg = 7'b1111101;
            4'h7: seg = 7'b0000111;
            4'h8: seg = 7'b1111111;
            4'h9: seg = 7'b1101111;
            4'ha: seg = 7'b1000000;   // '-'
            4'hb: seg = 7'b1111000;   // 't'
            4'hc: seg = 7'b1010000;   // 'r'
            default: seg = 7'b0000000;
        endcase
    end

    reg [7:0] uo_q;
    always @(posedge clk) begin
        if (rst) uo_q <= 8'd0;
        else     uo_q <= {dp, seg};
    end
    assign uo_out = uo_q;

    // ---------------------------------------------------------------- uio
    assign uio_out = {tx_busy, dir, toggle, ev_open, comp_s2, 3'b000};
    assign uio_oe  = oe ? 8'b1111_1000 : 8'b0000_0000;

    // keep lint quiet about the deliberately unused bits
    wire _unused = &{1'b0, uio_in[3], ev_close, q21[5:0], ev_score[6:5], 1'b0};
endmodule
