"""Attachment number c_hkl on an idealised node net (primer, Section 14).
c_hkl = largest number of links a node in the next layer forms with the crystal below a
plane parallel to (hkl). Phase 3 will derive the nets from the CIFs; here we use the ideal
node nets: pcu (MOF-5, Zn4O nodes) and fcu (UiO-66/67, Zr6/Hf6 nodes)."""
import itertools
import numpy as np

def net(kind, N=5):
    B = np.array(list(itertools.product(range(-N, N + 1), repeat=3)), float)
    if kind == "pcu":
        return B, 1.0
    if kind == "fcu":
        P = np.vstack([B + o for o in ([0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0])])
        return P, np.sqrt(2) / 2
    raise ValueError(kind)

def attachment_number(kind, hkl):
    P, nn = net(kind); n = np.array(hkl, float); n /= np.linalg.norm(n)
    P = P[np.linalg.norm(P, axis=1) < 4.0]
    h = np.round(P @ n, 6)
    crystal = P[h <= 0]; nxt = P[(h > 0) & (h <= 1.01)]
    nxt = nxt[np.linalg.norm(nxt - np.outer(nxt @ n, n), axis=1) < 1.5]
    return max(int(np.sum(np.abs(np.linalg.norm(crystal - s, axis=1) - nn) < 1e-6)) for s in nxt)
