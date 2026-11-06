import sys, klayout.db as db
lvs = db.LayoutVsSchematic(); lvs.read(sys.argv[1])
x = lvs.xref()
M = db.NetlistCrossReference.Match
for cp in x.each_circuit_pair():
    print("pair", cp.first().name if cp.first() else None, cp.second().name if cp.second() else None, cp.status())
    for p in x.each_net_pair(cp):
        if p.status() != M: print("  net", p.first().expanded_name() if p.first() else None, '|', p.second().expanded_name() if p.second() else None, p.status())
    for p in x.each_device_pair(cp):
        if p.status() != M:
            f, s = p.first(), p.second()
            print("  dev", (f.expanded_name(), f.device_class().name, f.trans) if f else None, '|', (s.expanded_name(), s.device_class().name) if s else None, p.status())
    for p in x.each_pin_pair(cp):
        if p.status() != M: print("  pin", p.first().name() if p.first() else None, p.second().name() if p.second() else None, p.status())
