"""Checks of the Phase-3 graph quantities against textbook nets with known answers."""
import sys, os, math, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mofmorph.graphfaces import PeriodicGraph, classify, contract_two_connected

ok = True
def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m); ok &= bool(c)

def build(P, L, dist):
    E, seen = [], set()
    for i, x in enumerate(P):
        for j, y in enumerate(P):
            for t in itertools.product([-1, 0, 1], repeat=3):
                v = y + np.array(t) @ L - x
                if abs(np.linalg.norm(v) - dist) < 1e-6:
                    if (j, i, tuple(-a for a in t)) in seen: continue
                    seen.add((i, j, t)); E.append((i, j, t))
    return PeriodicGraph(L, np.asarray(P) @ L, E)

r2, r3 = math.sqrt(2), math.sqrt(3)
pcu = PeriodicGraph(np.eye(3), [[0, 0, 0]], [(0, 0, (1, 0, 0)), (0, 0, (0, 1, 0)), (0, 0, (0, 0, 1))])
fcu = build(np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]]), np.eye(3), 1 / r2)
bcc = build(np.array([[0, 0, 0], [.5, .5, .5]]), np.eye(3), r3 / 2)
cases = [("pcu (Kossel crystal)", pcu, {(1,0,0): (1, 1.0, "F"), (1,1,0): (r2/2, 2.0, "S"), (1,1,1): (1/r3, 3.0, "K")}),
         ("fcu (fcc)", fcu, {(1,0,0): (.5, 4.0, "F"), (1,1,0): (1/(2*r2), 5.0, "S"), (1,1,1): (1/r3, 3.0, "F")}),
         ("bcc", bcc, {(1,1,0): (1/r2, 2.0, "F"), (1,0,0): (.5, 4.0, "K")})]
for name, G, faces in cases:
    for hkl, (d, E, cls) in faces.items():
        q = classify(G, np.array(hkl, float), d)
        check(abs(q["E_att"] - E) < 1e-9 and q["class"] == cls, f"{name} {hkl}: E_att={q['E_att']:.3f} (expect {E}), {q['class']} (expect {cls})")
# broken-bond surface energies, fcc: gamma100/gamma111 = 2/sqrt3 (classic nearest-neighbour result)
g100 = classify(fcu, np.array([1., 0, 0]), .5)["gamma_min"]; g111 = classify(fcu, np.array([1., 1, 1]), 1 / r3)["gamma_min"]
check(abs(g100 / g111 - 2 / r3) < 1e-9, f"fcc broken bonds: gamma100/gamma111 = {g100/g111:.4f} (2/sqrt3 = {2/r3:.4f})")
check(abs(g100 - 8) < 1e-9, f"fcc gamma100 = 4 bonds x 2 atoms per a^2 = 8 (got {g100})")
# contraction: pcu nodes with a 2-connected linker on every edge -> pcu again
L = np.eye(3); X = [[0, 0, 0], [.5, 0, 0], [0, .5, 0], [0, 0, .5]]
E = [(0, 1, (0, 0, 0)), (1, 0, (1, 0, 0)), (0, 2, (0, 0, 0)), (2, 0, (0, 1, 0)), (0, 3, (0, 0, 0)), (3, 0, (0, 0, 1))]
H = contract_two_connected(PeriodicGraph(L, X, E, ["node", "linker", "linker", "linker"]))
check(len(H.X) == 1 and len(H.edges) == 3 and H.degrees() == [6], "contracting ditopic linkers of decorated pcu gives pcu")
print("\nALL PASS" if ok else "\nSOME FAILED")
sys.exit(0 if ok else 1)
