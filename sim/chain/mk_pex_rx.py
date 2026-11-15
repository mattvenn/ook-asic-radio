"""Swap the extracted RX block (layout/pex/rx_t.spice: the tall chain, its one-row detector and the tap
wiring between them, as placed in the tile) into a chain testbench netlist.

    python3 sim/chain/mk_pex_rx.py <tb.spice> <out.spice> [--rx=layout/pex/rx_t.spice] [--ibias-det=2u]

tb_chain (no detector of its own: stability, chain MC, lna_lo): the chain subckt 'lna_chain' becomes a
wrapper with the same ports around rx_t, so the instance line and every script that edits it
(sim/chain/stability.sh: VSS -> gchip) work unchanged. Inside the wrapper the detector is live, as on
the chip: its supply VDDD on the chain's VDD, its bias an ideal ibias_det into the Mbias diode (the
testbench value, 2 uA), and Cdet (cdet_t, layout/ref/cdet_t.spice) on det, which nothing reads.

tb_logdet (dipole -> pad -> chain -> log_det; noise_tran, cw_drop): the chain instance x1 and the
detector instance x2 (log_det) become one rx_t instance on x2's det / ibias_det / VDD nets, plus Cdet;
the testbench's own Ibd keeps biasing it, and v(det) is rx_t's detector output.

The schematic subckts the swap replaces (lna_chain and its stages, log_det, det_cell, lna_shunt) are
removed; x1's instance parameters go (the extraction has none)."""
import re
import sys

ROOT_REL = '../..'
CHAIN_PORTS = 'inp inn ibias vcm lna_lo_n outp outn o1p o1n o2p o2n o3p o3n o4p o4n o5p o5n'.split()
DROP = ('lna_chain', 'amp_dp', 'amp_dpc', 'lna_shunt', 'log_det', 'det_cell')


def subckt(name, text):
    m = re.search(rf'^\.subckt {name}\s.*?^\.ends[^\n]*\n', text, flags=re.S | re.M)
    assert m, f'no .subckt {name}'
    return m.group(0)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    src, out = args
    rx = open(opt.get('rx', 'layout/pex/rx_t.spice')).read()
    cdet = subckt('cdet_t', open('layout/ref/cdet_t.spice').read())
    ibd = opt.get('ibias-det', '2u')
    s = open(src).read().replace('\n+', ' ')
    head = re.search(r'^\.subckt rx_t (.*)$', rx, re.M).group(1).split()
    assert head == CHAIN_PORTS + ['ibias_det', 'det', 'VDD', 'VSS', 'VDDD'], head

    x1 = re.search(r'^x1 (.*?) lna_chain\b.*$', s, re.M)
    assert x1, 'no x1 ... lna_chain instance'
    x2 = re.search(r'^x2 (.*?) log_det\b.*$', s, re.M)
    for c in DROP:
        s = re.sub(rf'^\.subckt {c}\s.*?^\.ends[^\n]*\n', '', s, flags=re.S | re.M)
    lib = rx + '\n' + cdet + '\n'
    if x2 is None:
        # tb_chain: a same-port wrapper, detector live inside it
        lib += ('* the chain as the testbench sees it: rx_t with its detector biased and loaded as in the tile\n'
                f'.subckt lna_chain {" ".join(CHAIN_PORTS)} VDD VSS\n'
                f'xrx {" ".join(CHAIN_PORTS)} ibias_det det VDD VSS VDD rx_t\n'
                f'Ibd VDD ibias_det {ibd}\n'
                'xcdet det VDD cdet_t\n'
                '.ends\n')
        s = re.sub(r'^(x1 .*? lna_chain)\b.*$', r'\1', s, flags=re.M)
    else:
        # tb_logdet: one rx_t instance on the chain's nets and the detector's det / ibias_det / VDD
        cn = x1.group(1).split()
        assert len(cn) == len(CHAIN_PORTS) + 2, cn
        dn = x2.group(1).split()            # t1p .. t6n (12) ibias_det det VDD VSS
        assert len(dn) == 16, dn
        ib, det, vddd = dn[12], dn[13], dn[14]
        sig, vdd, vss = cn[:len(CHAIN_PORTS)], cn[-2], cn[-1]
        # rx_t ports: the chain's signals, ibias_det det, VDD VSS (the chain's), VDDD (the detector's)
        s = s.replace(x1.group(0), f'x1 {" ".join(sig)} {ib} {det} {vdd} {vss} {vddd} rx_t')
        s = s.replace(x2.group(0), f'xcdet {det} {vddd} cdet_t')
    # the library goes in where the first dropped subckt was: before .end, after the testbench body
    s = re.sub(r'^\.end\s*$', lib.replace('\\', '\\\\') + '.end', s, count=1, flags=re.M)
    keep = ('lna_chain',) if x2 is None else ()      # tb_chain: x1 now names the wrapper
    for c in DROP:
        if c not in keep:
            assert not re.search(rf'^x\S* .* {c}$', s, re.M), f'an instance of {c} is left'
    open(out, 'w').write(s)


if __name__ == '__main__':
    main()
