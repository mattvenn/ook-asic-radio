"""
cocotb tests for radio_digital against the bit-exact model's vectors
(test/vectors/*.npz, see vectors/README.md).

Alignment (documented in radio_digital.v): rst_n is released at a falling
edge F0; call the next rising edge E1. Sample i is processed at rising edge
E(1 + 130*(i+1)), using comp_in as it was 2 edges earlier (synchroniser).
The testbench changes comp_in on the falling edge just after each tick and
reads trim_out on the falling edge just after the next tick.
"""
import os

import numpy as np
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

HERE = os.path.dirname(os.path.abspath(__file__))
# GL=1 (make GL=1): gate-level netlist. Internal signals don't survive
# synthesis, so the monitors use pins only: event close = falling edge of
# uio_out[4] (ev_open), score = the 7-seg digit, LED = uo_out[7] (DP).
GL = os.environ.get('GL') == '1'
PINMON = GL or os.environ.get('PINMON') == '1'      # pin monitors on RTL too, to validate them
SEG = [0b0111111, 0b0000110, 0b1011011, 0b1001111, 0b1100110,
       0b1101101, 0b1111101, 0b0000111, 0b1111111, 0b1101111]


def score_digit(score):
    """radio_digital.v: digit = ((score[4:0] - 1) mod 32) * 21 >> 6."""
    return ((((score & 31) - 1) & 31) * 21) >> 6
VEC = os.path.join(HERE, 'vectors')

T_NS = 100            # 10 MHz
SAMPLE = 130
CHIP = 1040
PERIOD = 191
BURSTS = 3


def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, T_NS, unit='ns').start())


async def reset(dut, role=0, code=0, uio=0, cycles=10):
    """Hold reset with the straps applied, release on a falling edge and
    return after the falling edge following E1."""
    dut.ui_in.value = (role << 7) | code
    dut.uio_in.value = uio
    dut.comp_in.value = 0
    dut.rst_n.value = 0
    for _ in range(cycles):
        await FallingEdge(dut.clk)
    assert int(dut.uio_oe.value) == 0, 'uio_oe must be 0 during reset'
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)          # just after E1


async def run_rx_vector(dut, name):
    d = np.load(os.path.join(VEC, f'rx_{name}.npz'))
    comp, trim, code = d['comp'], d['trim'], int(d['code'])
    exp_events = [tuple(map(int, e)) for e in d['events'].reshape(-1, 2)]
    exp_toggles = [int(t) for t in d['toggles']]

    start_clock(dut)
    await reset(dut, role=0, code=code)
    assert int(dut.rx_en.value) == 1 and int(dut.tx_en.value) == 0

    state = {'i': -1}
    events, toggles = [], []

    async def mon_events():
        while True:
            await RisingEdge(dut.u_rx.ev_close)
            i = state['i']
            assert i % 8 == 0, f'event closed at sample {i}, not a chip tick'
            events.append((i // 8 + 1 - 8, int(dut.u_rx.ev_score.value)))

    async def mon_toggles():
        while True:
            await dut.u_rx.led.value_change
            i = state['i']
            toggles.append(i // 8 + 1 - 8)

    async def mon_events_gl():
        prev = 0
        while True:
            await dut.uio_out.value_change
            now = (int(dut.uio_out.value) >> 4) & 1
            if prev and not now:                       # event closed
                i = state['i']
                assert i % 8 == 0, f'event closed at sample {i}, not a chip tick'
                for _ in range(3):                     # recent -> sym -> uo_q
                    await FallingEdge(dut.clk)
                seg = int(dut.uo_out.value) & 0x7f
                events.append((i // 8 + 1 - 8, SEG.index(seg) if seg in SEG else -seg))
            prev = now

    async def mon_toggles_gl():
        prev = 0
        while True:
            await dut.uo_out.value_change
            now = int(dut.uo_out.value) >> 7
            if now != prev:
                toggles.append(state['i'] // 8 + 1 - 8)
            prev = now

    if PINMON:
        exp_events = [(c, score_digit(sc)) for c, sc in exp_events]
        mon_events, mon_toggles = mon_events_gl, mon_toggles_gl

    m1 = cocotb.start_soon(mon_events())
    m2 = cocotb.start_soon(mon_toggles())

    mism = 0
    for i in range(len(comp)):
        dut.comp_in.value = int(comp[i])
        await Timer(SAMPLE * T_NS, unit='ns')      # falling edge after tick i
        state['i'] = i
        got = int(dut.trim_out.value)
        if got != int(trim[i]):
            mism += 1
            if mism < 5:
                dut._log.error(f'{name}: sample {i}: trim {got} != {int(trim[i])}')
    # let the last event close / pairing settle (nothing pending in vectors)
    await Timer(4 * T_NS, unit='ns')
    m1.cancel()
    m2.cancel()

    dut._log.info(f'{name}: {len(comp)} samples, trim mismatches {mism}, '
                  f'events {events}, toggles {toggles}')
    assert mism == 0, f'{name}: {mism} trim mismatches'
    assert events == exp_events, f'{name}: events {events} != {exp_events}'
    assert toggles == exp_toggles, f'{name}: toggles {toggles} != {exp_toggles}'
    assert int(dut.uo_out.value) >> 7 == len(exp_toggles) % 2, 'DP must show the LED state'


def rx_test(name):
    async def t(dut):
        await run_rx_vector(dut, name)
    t.__name__ = f'test_rx_{name}'
    t.__qualname__ = t.__name__
    return cocotb.test()(t)


for _n in ('clean', 'holdoff', 'two_sends', 'strong', 'weak', 'wrong_code',
           'bursty', 'fading', 'no_signal'):
    globals()[f'test_rx_{_n}'] = rx_test(_n)


# ------------------------------------------------------------------ TX
TX = np.load(os.path.join(VEC, 'tx_codes.npz'))


def send_chips(code):
    one = np.concatenate([TX['chips'][code], np.zeros(PERIOD - 127, np.uint8)])
    return np.tile(one, BURSTS)


async def check_send(dut, code, timeout_chips=200):
    """Wait for uio_out[7] (TX sending) to rise, then check tx_en at every chip
    centre of the 3-burst send and that sending ends after it."""
    for _ in range(timeout_chips * CHIP):
        await FallingEdge(dut.clk)
        if (int(dut.uio_out.value) >> 7) & 1:
            break
    else:
        assert False, f'code {code}: no send started'
    # busy rose at edge S (one clock before this falling edge); tx_en follows
    # the chip value one clock after each chip boundary
    await Timer(CHIP // 2 * T_NS, unit='ns')
    exp = send_chips(code)
    got = []
    seg_seen = set()
    for n in range(len(exp)):
        got.append(int(dut.tx_en.value))
        seg_seen.add(int(dut.uo_out.value) & 0x7f)
        await Timer(CHIP * T_NS, unit='ns')
    got = np.array(got, np.uint8)
    bad = np.nonzero(got != exp)[0]
    assert len(bad) == 0, f'code {code}: tx_en wrong at chips {bad[:10]}'
    assert (int(dut.uio_out.value) >> 7) & 1 == 0, 'still sending after 3 bursts'
    assert int(dut.tx_en.value) == 0
    # 7-seg showed '1', '2', '3' while sending
    assert {0b0000110, 0b1011011, 0b1001111} <= seg_seen, seg_seen


@cocotb.test()
async def test_tx_codes(dut):
    """Send on reset release for several codes, bit-exact vs tx_codes.npz."""
    start_clock(dut)
    for code in (0, 0x5A, 126, 127, 1, 0x11):
        await reset(dut, role=1, code=code)
        assert int(dut.rx_en.value) == 0
        await check_send(dut, code, timeout_chips=2)
        # precomputed LFSR2 start matches the model
        if code != 127 and not GL:
            assert int(dut.u_gold.l2_start.value) == int(TX['lfsr2'][code])
        # no second send without a code change
        for _ in range(60):
            await Timer(CHIP * T_NS, unit='ns')
            assert (int(dut.uio_out.value) >> 7) & 1 == 0
        dut._log.info(f'code {code}: send OK')


@cocotb.test()
async def test_tx_code_change(dut):
    """A code change (with bounce) sends again after ~50 ms debounce."""
    start_clock(dut)
    await reset(dut, role=1, code=0x5A)
    await check_send(dut, 0x5A, timeout_chips=2)
    # bounce: 0x33 briefly, then 0x2C for good
    dut.ui_in.value = (1 << 7) | 0x33
    await Timer(20 * CHIP * T_NS, unit='ns')
    dut.ui_in.value = (1 << 7) | 0x2C
    t0 = cocotb.utils.get_sim_time('ns')
    await check_send(dut, 0x2C, timeout_chips=60)
    # started ~48-49 chips after the last change, not before
    dt = (cocotb.utils.get_sim_time('ns') - t0) / (CHIP * T_NS) - BURSTS * PERIOD - 0.5
    dut._log.info(f'send started {dt:.1f} chips after the code change')
    assert 47 <= dt <= 51, dt


@cocotb.test()
async def test_raw_and_straps(dut):
    """Mode strap: magic 1010 on uio[7:4] + mode 01 -> raw TX. Raw RX bit on
    uio_out[3] in all modes. Without the magic, code mode."""
    start_clock(dut)
    # raw TX (role TX), uio[2] keys tx_en
    await reset(dut, role=1, code=5, uio=0b1010_0001)
    dut.uio_in.value = 0
    await FallingEdge(dut.clk)                # oe is enabled one clock after E1
    assert int(dut.uio_oe.value) == 0b1111_1000
    for v in (1, 0, 1, 1, 0):
        dut.uio_in.value = v << 2
        await Timer(1, unit='ns')
        assert int(dut.tx_en.value) == v
        await FallingEdge(dut.clk)
    # raw RX bit = comp_in delayed by the 2-flop synchroniser
    for v in (1, 0, 1):
        dut.comp_in.value = v
        for _ in range(3):
            await FallingEdge(dut.clk)
        assert (int(dut.uio_out.value) >> 3) & 1 == v
    # no magic: mode bits ignored -> code mode, uio[2] does not key the TX
    await reset(dut, role=1, code=5, uio=0b0000_0001)
    dut.uio_in.value = 0b100
    for _ in range(300):                      # send starts at the first chip tick
        await FallingEdge(dut.clk)
        if not GL:
            assert int(dut.tx_en.value) == int(dut.u_tx.tx_en.value)
    assert (int(dut.uio_out.value) >> 7) & 1 == 1   # code-mode send in progress (tx_busy)
    # both arms follow tx_en by default
    assert int(dut.tx_en_n.value) == int(dut.tx_en.value)


@cocotb.test()
async def test_single_ended_strap(dut):
    """uio[3] with the magic -> single-ended: tx_en_n held 0 while tx_en keys.
    Without the magic uio[3] is ignored (both arms)."""
    start_clock(dut)
    for uio, se in ((0b1010_1001, 1), (0b0000_1001, 0), (0b1010_0001, 0)):
        await reset(dut, role=1, code=5, uio=uio)
        dut.uio_in.value = 0
        raw = (uio >> 4) == 0b1010
        for v in (1, 0, 1):
            if raw:                            # raw TX: key directly
                dut.uio_in.value = v << 2
                await Timer(1, unit='ns')
            else:                              # code mode: wait for a send to key
                for _ in range(8 * CHIP):
                    await FallingEdge(dut.clk)
                    if int(dut.tx_en.value) == v:
                        break
            assert int(dut.tx_en.value) == v
            assert int(dut.tx_en_n.value) == (v & (1 - se)), f'uio {uio:08b} v {v}'
            await FallingEdge(dut.clk)


@cocotb.test()
async def test_debug_strap(dut):
    """uio[2] with the magic at reset -> dbg_en (det on ua[2]); without the
    magic, or with uio[2] = 0, off. Independent of role, mode and uio after reset."""
    start_clock(dut)
    for role, uio, want in ((0, 0b1010_0100, 1), (1, 0b1010_0101, 1), (0, 0b0000_0100, 0),
                            (0, 0b1010_0000, 0), (1, 0b1010_1001, 0)):
        await reset(dut, role=role, code=5, uio=uio)
        for v in (0, 0b100, 0xff):                # later uio activity doesn't change it
            dut.uio_in.value = v
            await FallingEdge(dut.clk)
            assert int(dut.dbg_en.value) == want, f'role {role} uio {uio:08b}'


@cocotb.test()
async def test_sc_phases(dut):
    """sc_phi1/sc_phi2 non-overlapping, one cycle per 130-clock sample."""
    start_clock(dut)
    await reset(dut, role=0, code=1)
    p1, p2 = [], []
    for _ in range(3 * SAMPLE):
        await FallingEdge(dut.clk)
        p1.append(int(dut.sc_phi1.value))
        p2.append(int(dut.sc_phi2.value))
    p1, p2 = np.array(p1), np.array(p2)
    assert not np.any(p1 & p2), 'phases overlap'
    # dead time >= 2 clocks between phases
    both = p1 | p2
    assert np.sum(p1[SAMPLE:2 * SAMPLE]) > 50 and np.sum(p2[SAMPLE:2 * SAMPLE]) > 50
    assert np.sum(both[SAMPLE:2 * SAMPLE] == 0) >= 4
    rises = np.nonzero(np.diff(p1) == 1)[0]
    assert np.all(np.diff(rises) == SAMPLE), rises
