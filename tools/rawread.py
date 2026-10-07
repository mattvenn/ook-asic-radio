"""
Minimal reader for ngspice raw files (binary or ascii, real or complex).

    from rawread import read_raw
    plots = read_raw('build/tb_input_ac.raw')   # list of plots
    p = plots[0]; p['vars'] -> {name: np.array}, p['scale'] -> name of x axis
"""
import numpy as np


def read_raw(path):
    plots = []
    with open(path, 'rb') as fh:
        data = fh.read()
    pos = 0
    while pos < len(data):
        hdr = {}
        names = []
        while True:
            end = data.index(b'\n', pos)
            line = data[pos:end].decode('latin-1')
            pos = end + 1
            if line.startswith('Variables:'):
                nvars = int(hdr['No. Variables'])
                for _ in range(nvars):
                    end = data.index(b'\n', pos)
                    parts = data[pos:end].decode('latin-1').split()
                    pos = end + 1
                    names.append(parts[1])
                continue
            if line.startswith('Binary:') or line.startswith('Values:'):
                binary = line.startswith('Binary:')
                break
            if ':' in line:
                k, v = line.split(':', 1)
                hdr[k.strip()] = v.strip()
        npts = int(hdr['No. Points'])
        cplx = 'complex' in hdr.get('Flags', '')
        nv = len(names)
        if binary:
            dt = np.complex128 if cplx else np.float64
            n = npts * nv
            arr = np.frombuffer(data, dtype=dt, count=n, offset=pos).reshape(npts, nv)
            pos += n * np.dtype(dt).itemsize
        else:
            vals = []
            for _ in range(npts):
                row = []
                for _ in range(nv):
                    end = data.index(b'\n', pos)
                    tok = data[pos:end].decode().split()[-1]
                    pos = end + 1
                    row.append(complex(*map(float, tok.split(','))) if cplx else float(tok))
                vals.append(row)
            arr = np.array(vals)
        plots.append({'title': hdr.get('Plotname', ''), 'scale': names[0],
                      'vars': {nm: arr[:, i] for i, nm in enumerate(names)}})
        while pos < len(data) and data[pos:pos + 1] in (b'\n', b'\r'):
            pos += 1
    return plots
