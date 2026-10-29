# Flatten layout/lna_chain.gds into build/kpex/lna_chain_flat.gds.
# Stage-internal labels (sn, sp, tail) get the stage prefix (st1_tail, st5_sn, ...);
# the stages' own port labels are dropped (the top-level labels name those nets).
import klayout.db as db
PORTS = {'inp', 'inn', 'outp', 'outn', 'nb', 'VDD', 'VSS'}
l = db.Layout(); l.read('layout/lna_chain.gds')
top = l.cell('lna_chain')
def stage(inst):
    b = inst.bbox(); x0 = b.left / 1000; y0 = b.bottom / 1000
    if inst.cell.name == 'amp_dp': return 'st1'
    if inst.cell.name != 'amp_dpc': return None
    if y0 > 30: return 'st2'
    return {107.42: 'st3', 74.88: 'st4', 42.34: 'st5', 9.8: 'st6'}[round(x0, 2)]
names = {}
for inst in top.each_inst():
    s = stage(inst)
    if s: names[(inst.cell.name, str(inst.trans))] = s
print(names)
# collect texts to re-add after flattening
add = []
for inst in top.each_inst():
    s = names.get((inst.cell.name, str(inst.trans)))
    if not s: continue
    for li in l.layer_indexes():
        it = inst.cell.begin_shapes_rec(li)
        while not it.at_end():
            sh = it.shape()
            if sh.is_text():
                t = sh.text.transformed(inst.cplx_trans * it.trans())
                if t.string not in PORTS:
                    t.string = f'{s}_{t.string}'
                    add.append((li, t))
            it.next()
# remove all texts in child cells, then flatten
for c in l.each_cell():
    if c.cell_index() == top.cell_index(): continue
    for li in l.layer_indexes():
        c.shapes(li).each(db.Shapes.STexts) and None
        sh = c.shapes(li)
        for s_ in list(sh.each(db.Shapes.STexts)):
            sh.erase(s_)
top.flatten(-1, True)
for li, t in add:
    top.shapes(li).insert(t)
print('added', sorted(set(t.string for _, t in add)))
l.write('build/kpex/lna_chain_flat.gds')
