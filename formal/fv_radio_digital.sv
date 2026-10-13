`default_nettype none
// Formal harness for radio_digital (SymbiYosys: formal/radio_digital.sby).
// Every input is free (straps, code, comparator, rst_n at any time); the only
// assumption is reset in the first cycle. The RTL is not modified: internal
// signals reach fv_props' s_* ports through `connect -set` in the .sby script
// (Yosys has no hierarchical references), after flatten. The ports are left
// open here: `connect -set` cuts every existing connection with its target on
// the left, and flatten / proc store theirs that way.
//
//   1  TX / RX safety: never transmit while receiving, debug gate only with the strap
//   2  correlator timing that rd_corr / rd_rx rely on (comments there)
//   6  switched-cap clocks: non-overlapping, >= 4 clocks dead, off with RX off
module fv_radio_digital (
    input wire       clk,
    input wire       rst_n,
    input wire [7:0] ui_in,
    input wire [7:0] uio_in,
    input wire       comp_in
);
    wire [7:0] uo_out, uio_out, uio_oe, trim_out;
    wire       tx_en, tx_en_n, rx_en, dbg_en, sc_phi1, sc_phi2;

    radio_digital dut (
        .clk(clk), .rst_n(rst_n), .ui_in(ui_in), .uio_in(uio_in),
        .uo_out(uo_out), .uio_out(uio_out), .uio_oe(uio_oe),
        .comp_in(comp_in), .trim_out(trim_out),
        .tx_en(tx_en), .tx_en_n(tx_en_n), .rx_en(rx_en), .dbg_en(dbg_en),
        .sc_phi1(sc_phi1), .sc_phi2(sc_phi2)
    );

    fv_props chk (
        .clk(clk), .rst_n(rst_n), .ui_in(ui_in), .uio_in(uio_in),
        .tx_en(tx_en), .tx_en_n(tx_en_n), .rx_en(rx_en), .dbg_en(dbg_en),
        .sc_phi1(sc_phi1), .sc_phi2(sc_phi2)
        // s_* left open: driven from the DUT's internals by `connect -set` in the .sby
    );
endmodule

module fv_props (
    input wire       clk,
    input wire       rst_n,
    input wire [7:0] ui_in,
    input wire [7:0] uio_in,
    input wire       tx_en, tx_en_n, rx_en, dbg_en, sc_phi1, sc_phi2,
    // probes into the DUT (see the .sby)
    input wire       s_rst,      // dut.rst: rst_n registered
    input wire       s_wend,     // dut.u_corr.wend: a chip window ends, popcount starts
    input wire       s_busy,     // dut.u_corr.busy: popcount running
    input wire       s_clr,      // dut.u_corr.clr: chip registers clearing after reset
    input wire       s_done,     // dut.u_corr.done: score valid
    input wire       s_closing   // dut.u_rx.closing: an event closes this clock
);
    // ---------------------------------------------------------------- reset
    reg f_init = 1'b1;
    always @(posedge clk) f_init <= 1'b0;
    always @(*) if (f_init) assume (!rst_n);

    // the spec's view of the straps, latched while the DUT's reset register
    // (rst_n delayed one clock) is high
    reg f_seen = 1'b0;          // a reset has been seen (registers defined)
    reg f_role_tx, f_raw, f_dbg;
    always @(posedge clk) begin
        if (s_rst) begin
            f_seen    <= 1'b1;
            f_role_tx <= ui_in[7];
            f_raw     <= (uio_in[7:4] == 4'b1010) && (uio_in[1:0] == 2'b01);
            f_dbg     <= (uio_in[7:4] == 4'b1010) && uio_in[2];
        end
    end
    // the reset register follows rst_n
    reg f_rstn_q = 1'b0, f_v = 1'b0;
    always @(posedge clk) begin
        f_rstn_q <= rst_n;
        f_v      <= 1'b1;
    end
    always @(*) if (f_v) assert (s_rst == !f_rstn_q);
    wire f_on = f_seen && !s_rst;    // out of reset, straps latched

    // ---------------------------------------------------------------- 1: safety
    always @(*) if (f_seen) begin
        // role: RX powered exactly when the role strap said RX
        assert (rx_en == !f_role_tx);
        // the n arm is never on without the p arm (single-ended only drops n)
        assert (!tx_en_n || tx_en);
        // debug gate only with the magic + debug strap
        assert (dbg_en == f_dbg);
    end
    // never transmit while receiving, in code mode
    always @(*) if (f_on && !f_raw) assert (!(rx_en && tx_en));
`ifdef FV_RAW_RX
    // the same in every mode (expected to fail: raw mode keys tx_en from
    // uio_in[2] whatever the role; intended, a loopback test, docs/info.md)
    always @(*) if (f_on) assert (!(rx_en && tx_en));
`endif

    // ---------------------------------------------------------------- 2: correlator timing
    // clocks since the last popcount start (wend while idle), saturating
    reg [7:0] f_since = 8'hff;
    always @(posedge clk)
        if (s_rst)                          f_since <= 8'hff;
        else if (s_wend && !s_busy && !s_clr) f_since <= 8'd0;
        else if (f_since != 8'hff)          f_since <= f_since + 8'd1;

    always @(*) if (f_on) begin
        // a window never ends while the popcount or the post-reset clear runs
        // (its chip bit would not be shifted in)
        assert (!(s_wend && (s_busy || s_clr)));
        // a score never arrives in the clock an event closes (the open would be lost)
        assert (!(s_done && s_closing));
        // the score comes exactly 128 clocks after the window end, and only then
        assert (s_done == (f_since == 8'd127));
    end

    // ---------------------------------------------------------------- 6: switched-cap clocks
    // clocks since each phase was last high: 0 = it was high in the previous clock (saturating at 15)
    reg [3:0] f_lo1 = 4'hf, f_lo2 = 4'hf;
    reg [3:0] f_ra = 4'd0;      // clocks since the DUT's reset register was high (saturating)
    always @(posedge clk) begin
        f_ra  <= s_rst ? 4'd0 : (f_ra == 4'hf ? 4'hf : f_ra + 4'd1);
        f_lo1 <= sc_phi1 ? 4'd0 : (f_lo1 == 4'hf ? 4'hf : f_lo1 + 4'd1);
        f_lo2 <= sc_phi2 ? 4'd0 : (f_lo2 == 4'hf ? 4'hf : f_lo2 + 4'd1);
    end
    always @(*) if (f_seen) begin
        assert (!(sc_phi1 && sc_phi2));
        // >= 4 clocks with both low between one phase and the other
        // (f_lo = number of clocks since the phase was last high), unless a
        // reset came in between: a 1-clock reset clears a high phase and the
        // other rises 2 clocks later (found by the proof; still no overlap)
        if (sc_phi2 && f_ra > f_lo1) assert (f_lo1 >= 4'd4);
        if (sc_phi1 && f_ra > f_lo2) assert (f_lo2 >= 4'd4);
        // both off when RX is off
        if (!rx_en) assert (!sc_phi1 && !sc_phi2);
    end
endmodule
