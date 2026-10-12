"""
cocotb smoke tests at the TT level (tt_um_mattvenn_radio, wrapper generated from the top
schematic by tools/check_pinout.py): three of verilog/test/test_radio.py's tests, run
through the TT pins, plus the uio_oe directions against info.yaml.

test_radio's tests are written for the bare macro. TTPins gives them the TT pins for the
TT signals and, for the macro <-> analog signals, the analog stub's side of each net
(xana's ports), so every value goes through the schematic's wiring.
"""
import cocotb
from cocotb.triggers import FallingEdge

import check_pinout
import test_radio

# macro signal -> the analog stub's port on the same net
ANALOG = {'comp_in': 'comp_r', 'trim_out': 'trim', 'tx_en': 'tx_en', 'tx_en_n': 'tx_en_n',
          'rx_en': 'rx_en', 'dbg_en': 'dbg_en', 'sc_phi1': 'sc_phi1', 'sc_phi2': 'sc_phi2'}
TT = ('clk', 'rst_n', 'ui_in', 'uio_in', 'uo_out', 'uio_out', 'uio_oe')


class TTPins:
    """Looks like test_radio's radio_digital dut, backed by the TT-level testbench."""

    def __init__(self, tb):
        self._tb = tb
        self._log = tb._log
        self._ana = tb.user_project.xana
        self._dig = tb.user_project.xdig

    def __getattr__(self, name):
        if name in TT:
            return getattr(self._tb, name)
        if name in ANALOG:
            return getattr(self._ana, ANALOG[name])
        return getattr(self._dig, name)       # RTL internals (u_gold, u_tx), unused at GL


def adapt(t):
    async def run(dut):
        dut.ena.value = 1
        await t.func(TTPins(dut))
    run.__doc__ = t.func.__doc__
    run.__name__ = run.__qualname__ = t.func.__name__
    return cocotb.test()(run)


test_tx_codes = adapt(test_radio.test_tx_codes)
test_raw_and_straps = adapt(test_radio.test_raw_and_straps)
test_debug_strap = adapt(test_radio.test_debug_strap)


@cocotb.test()
async def test_uio_oe(dut):
    """uio_oe is 0 during reset, then 1 on exactly the uio pins info.yaml lists as outputs."""
    dut.ena.value = 1
    d = TTPins(dut)
    test_radio.start_clock(d)
    for role in (0, 1):
        await test_radio.reset(d, role=role, code=5)   # asserts uio_oe == 0 during reset
        await FallingEdge(dut.clk)
        got = int(dut.uio_oe.value)
        assert got == check_pinout.UIO_OE_OUT, f'role {role}: uio_oe {got:08b}, ' \
            f'info.yaml outputs {check_pinout.UIO_OE_OUT:08b}'
