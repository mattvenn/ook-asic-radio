# 3D finite-difference (cell-centred) DC conduction solve of the substrate under lna_chain.
# Ports = surface patches (geom.json) at unknown potential; p-taps = 0 V. Returns the port
# short-circuit admittance matrix Y (taps at 0): I = Y V.
#
#   build/substrate/venv/bin/python build/substrate/solve.py --h 1 --rho 20 --back neumann --T 300 --out run_h1
#
# Layers: p-well (rho_pw, 0..0.7 um) everywhere outside n-well; n-well columns are insulating
# for 0..0.8 um; bulk p (rho) below, to the backside at T (neumann = floating, dirichlet = 0 V).
import argparse, json, os, time, numpy as np, scipy.sparse as sp, pyamg
from scipy.sparse.linalg import cg

ap = argparse.ArgumentParser()
ap.add_argument('--h', type=float, default=1.0)            # lateral cell (um)
ap.add_argument('--rho', type=float, default=20.0)         # bulk, ohm-cm
ap.add_argument('--rsh_pw', type=float, default=3050.0)    # p-well sheet, ohm/sq
ap.add_argument('--t_pw', type=float, default=0.7)         # p-well depth, um
ap.add_argument('--t_nw', type=float, default=0.8)         # n-well depth, um
ap.add_argument('--T', type=float, default=300.0)          # die thickness, um
ap.add_argument('--back', default='neumann', choices=['neumann', 'dirichlet'])
ap.add_argument('--zgrow', type=float, default=1.35)
ap.add_argument('--drop_taps', default='')                 # 'moat': remove the moat ring's p-taps
ap.add_argument('--geom', default=os.path.join(os.path.dirname(__file__), 'geom.json'))
ap.add_argument('--out', required=True)
ap.add_argument('--tol', type=float, default=1e-9)
ap.add_argument('--nports', type=int, default=0)   # debug: solve only the first n ports
a = ap.parse_args()
D = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(D, a.out); os.makedirs(out, exist_ok=True)
t0 = time.time()
g = json.load(open(a.geom))
x0, y0, x1, y1 = g['domain']; h = a.h
nx, ny = int(round((x1 - x0) / h)), int(round((y1 - y0) / h))
xs = x0 + h * np.arange(nx + 1); ys = y0 + h * np.arange(ny + 1)

# z grid: p-well in cells of ~h/4 (>= 2), one cell to the n-well bottom, then geometric to T
npw = max(2, int(np.ceil(a.t_pw / (h / 4))))
z = list(np.linspace(0, a.t_pw, npw + 1)) + [a.t_nw]
dz = max(h / 4, 0.1)
while z[-1] < a.T:
    dz *= a.zgrow
    z.append(min(a.T, z[-1] + dz))
    if a.T - z[-1] < 0.5 * dz * a.zgrow: z[-1] = a.T
z = np.array(z); nz = len(z) - 1; dzs = np.diff(z); zc = 0.5 * (z[1:] + z[:-1])

def frac(boxes):
    """area fraction of each lateral cell covered by the boxes (boxes merged / non-overlapping)."""
    F = np.zeros((nx, ny))
    for bx0, by0, bx1, by1 in boxes:
        i0, i1 = max(0, int(np.floor((bx0 - x0) / h))), min(nx, int(np.ceil((bx1 - x0) / h)))
        j0, j1 = max(0, int(np.floor((by0 - y0) / h))), min(ny, int(np.ceil((by1 - y0) / h)))
        if i1 <= i0 or j1 <= j0: continue
        ox = np.clip(np.minimum(xs[i0 + 1:i1 + 1], bx1) - np.maximum(xs[i0:i1], bx0), 0, None)
        oy = np.clip(np.minimum(ys[j0 + 1:j1 + 1], by1) - np.maximum(ys[j0:j1], by0), 0, None)
        F[i0:i1, j0:j1] += np.outer(ox, oy) / (h * h)
    return F

def mark(boxes, thr=0.3):
    F = frac(boxes); M = F >= thr
    for b in boxes:                       # every shape gets at least its best cell
        f1 = frac([b])
        if not (M & (f1 > 0)).any() and f1.max() > 0: M[np.unravel_index(f1.argmax(), f1.shape)] = True
    return M

nw = frac(g['nwell']) >= 0.5
taps_boxes = g['ptap']
if a.drop_taps == 'moat':
    # the moat's p-tap ring: everything between the rows (block y 21..36)
    taps_boxes = [b for b in taps_boxes if not (b[1] >= 21 and b[3] <= 36 and b[0] >= -1 and b[2] <= 146.5)]
tap = mark(taps_boxes) & ~nw
names = list(g['ports'])
pid = -np.ones((nx, ny), int)
for k, n in enumerate(names):
    M = mark(g['ports'][n]) & ~nw & ~tap & (pid < 0)
    if not M.any(): raise SystemExit(f'port {n} got no cells')
    pid[M] = k
print(f'grid {nx} x {ny} x {nz} (h {h}, z {z[:npw + 3].round(3).tolist()}... {len(z)} planes to {z[-1]}), '
      f'taps {tap.sum()} cells, ports {len(names)}, n-well {nw.sum()} cells', flush=True)

# conductivity (S/um) per cell
sig_pw = 1.0 / (a.rsh_pw * a.t_pw * 1e-4 * 1e4)   # rho_pw [ohm-cm] = Rsh * t[cm]; S/um = 1/(rho*1e4)
sig_b = 1.0 / (a.rho * 1e4)
S = np.empty((nx, ny, nz))
S[:, :, :] = sig_b
S[:, :, zc < a.t_pw] = sig_pw
for k in np.where(zc < a.t_nw)[0]: S[nw, k] = 0.0
print(f'rho_pw {1 / (sig_pw * 1e4):.4f} ohm-cm, rho {a.rho} ohm-cm', flush=True)

N = nx * ny * nz
idx = np.arange(N).reshape(nx, ny, nz)
rows, cols, vals = [], [], []
def link(sl_a, sl_b, Gs):
    ia, ib = idx[sl_a].ravel(), idx[sl_b].ravel(); Gs = Gs.ravel(); m = Gs > 0
    rows.append(ia[m]); cols.append(ib[m]); vals.append(Gs[m])
def hm(s1, d1, s2, d2):     # series conductance per area of two half cells
    with np.errstate(divide='ignore', invalid='ignore'):
        r = d1 / (2 * s1) + d2 / (2 * s2)
        return np.where((s1 > 0) & (s2 > 0), 1.0 / r, 0.0)
DZ = dzs[None, None, :]
link((slice(0, -1), slice(None), slice(None)), (slice(1, None), slice(None), slice(None)), hm(S[:-1], h, S[1:], h) * h * DZ)
link((slice(None), slice(0, -1), slice(None)), (slice(None), slice(1, None), slice(None)), hm(S[:, :-1], h, S[:, 1:], h) * h * DZ)
link((slice(None), slice(None), slice(0, -1)), (slice(None), slice(None), slice(1, None)),
     hm(S[:, :, :-1], dzs[None, None, :-1], S[:, :, 1:], dzs[None, None, 1:]) * h * h)
r = np.concatenate(rows); c = np.concatenate(cols); v = np.concatenate(vals)
G = sp.coo_matrix((v, (r, c)), shape=(N, N)).tocsr(); G = G + G.T
diag = np.asarray(G.sum(axis=1)).ravel()
gback = np.zeros(N)
if a.back == 'dirichlet':
    gback[idx[:, :, -1].ravel()] = (S[:, :, -1] * h * h / (dzs[-1] / 2)).ravel()
L = sp.diags(diag + gback) - G          # nodal conductance matrix (all cells)

# fixed nodes: top-layer cells of taps (0 V) and ports
fixed = np.zeros(N, bool); fixed[idx[:, :, 0][tap]] = True
port_cells = [idx[:, :, 0][pid == k] for k in range(len(names))]
for pc in port_cells: fixed[pc] = True
live = (~fixed) & (diag > 0)
free = np.where(live)[0]
A = L[free][:, free].tocsr()
B = L[free]                              # coupling of free nodes to all
print(f'{len(free)} unknowns, nnz {A.nnz}; assembled in {time.time() - t0:.1f} s', flush=True)
t1 = time.time()
ml = pyamg.smoothed_aggregation_solver(A, symmetry='hermitian', max_coarse=500)
M = ml.aspreconditioner(cycle='V')
print(f'AMG setup {time.time() - t1:.1f} s, levels {len(ml.levels)}', flush=True)

P = len(names); Y = np.zeros((P, P)); iters = []
Lc = L.tocsr()
for k in range(P):
    V = np.zeros(N); V[port_cells[k]] = 1.0
    rhs = -(B @ V)
    it = [0]
    x, info = cg(A, rhs, rtol=a.tol, M=M, maxiter=500, callback=lambda xk: it.__setitem__(0, it[0] + 1))
    if info: print('  CG not converged for', names[k], info)
    print(f'  port {k} {names[k]}: {it[0]} iters, {time.time() - t1:.1f} s', flush=True)
    if a.nports and k + 1 >= a.nports: break
    V[free] = x
    I = Lc @ V                       # net current out of each node into the network
    for j in range(P): Y[j, k] = I[port_cells[j]].sum()
    iters.append(it[0])
gtap = -Y.sum(axis=0)   # current into the taps (+ backside) per volt on port k (all others 0)
print(f'{P} solves in {time.time() - t1:.1f} s (CG iters {min(iters)}..{max(iters)}); total {time.time() - t0:.1f} s', flush=True)
Ys = 0.5 * (Y + Y.T)
print('max asymmetry |Y-Y^T|/|Y|:', np.abs(Y - Y.T).max() / np.abs(Y).max())
np.save(os.path.join(out, 'Y.npy'), Ys)
json.dump({'names': names, 'args': vars(a), 'grid': [nx, ny, nz], 'z': z.tolist(),
           'unknowns': int(len(free)), 'time_s': time.time() - t0}, open(os.path.join(out, 'info.json'), 'w'))
Z = np.linalg.inv(Ys)
def show(n): return names.index(n)
for n in ['st1_mp', 'st1_mn', 'st1_mtail', 'st4_mn', 'st4_mtail_n', 'st6_mn', 'st6_mp', 'cin_p_11', 'rb_p']:
    k = show(n); print(f'  {n:12} Y_kk {Ys[k, k] * 1e3:8.4f} mS  R(others shorted) {1 / Ys[k, k]:9.1f}  Z_kk(others floating) {Z[k, k]:9.1f} ohm')
for a_, b_ in [('st6_mn', 'st1_mp'), ('st6_mp', 'st1_mn'), ('st6_mn', 'st1_mn'), ('st6_mtail_n', 'st1_mtail'), ('st6_mn', 'cin_p_11'), ('st6_mp', 'cin_n_11'), ('st5_mp', 'cin_n_10'), ('st2_mn', 'st1_mn')]:
    i, j = show(a_), show(b_)
    print(f'  {a_:12} -> {b_:12} R_link {-1 / Ys[i, j] if Ys[i, j] < 0 else float("inf"):12.4g} ohm   Z_transfer {Z[i, j]:9.4g} ohm')
