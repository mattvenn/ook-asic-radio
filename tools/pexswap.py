"""Swap schematic subckts in an xschem netlist for their extracted layouts.

    from pexswap import swap
    deck = swap(deck, ['tx_drv'])     # uses layout/pex/tx_drv.spice

Removes each '.subckt <block> ... .ends' from the deck and adds an .include of
layout/pex/<block>.spice (made by layout/pex.sh; same name and port order), so
every instance of the block uses the extracted R+C netlist. The include path
is relative to build/, where the decks run.
"""
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def swap(deck, blocks):
    for b in blocks:
        pex = os.path.join(ROOT, 'layout', 'pex', b + '.spice')
        if not os.path.exists(pex):
            raise FileNotFoundError(f'{pex}: run tools/osic bash layout/pex.sh {b}')
        pat = re.compile(rf'^\.subckt\s+{re.escape(b)}\s.*?^\.ends\b[^\n]*\n', re.S | re.M | re.I)
        deck, n = pat.subn('', deck)
        if n != 1:
            raise ValueError(f'{b}: found {n} schematic subckt definitions in the deck')
        inc = f'.include ../layout/pex/{b}.spice\n'
        deck = re.sub(r'^\.end\s*$', inc + '.end', deck, flags=re.M) if re.search(r'^\.end\s*$', deck, re.M) \
            else deck + inc
    return deck
