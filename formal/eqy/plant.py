#!/usr/bin/env python3
"""Make a planted-bug copy of the netlist, for the eqy self-test (run.sh).
Usage: plant.py <bug> nl.v > bug.v
Each bug is one exact text edit on radio_digital.nl.v (it must match exactly once)."""
import sys

BUGS = {
    # correlator: the chip registers' clock-gate enable (en0..en3 = clr | ...): or2 -> and2
    'corr_and': ('sky130_fd_sc_hd__or2_2 _0807_ (.A(rx_step),',
                 'sky130_fd_sc_hd__and2_2 _0807_ (.A(rx_step),'),
    # TX enable: the raw / code mode mux in front of tx_en with its inputs swapped
    'tx_mux': ('_0805_ (.A0(tx_code_en),\n    .A1(net13),',
               '_0805_ (.A0(net13),\n    .A1(tx_code_en),'),
    # deep in time: the popcount's top bit (acc[6]) reads acc[5]. Only differs once the count
    # passes 64 matches in a 127-clock rotation, so a simulation needs a strong burst to see it
    'acc_top': ('_1013_ (.A1_N(\\u_corr.acc[6] ),',
                '_1013_ (.A1_N(\\u_corr.acc[5] ),'),
    # clocking: one chip-register flop (sr0[5]) on register 1's gated clock instead of 0's
    'clk_swap': ('_1771_ (.CLK(\\clknet_4_8_0_u_corr.gclk0 ),',
                 '_1771_ (.CLK(\\clknet_4_10_0_u_corr.gclk1 ),'),
}

bug, path = sys.argv[1], sys.argv[2]
old, new = BUGS[bug]
txt = open(path).read()
if txt.count(old) != 1:
    sys.exit(f'plant.py: {bug}: the edit matches {txt.count(old)} times in {path}')
sys.stdout.write(txt.replace(old, new))
