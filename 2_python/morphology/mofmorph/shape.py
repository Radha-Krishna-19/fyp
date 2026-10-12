"""Crystal shape as a convex polytope  P = {x : n_f . x <= r_f}  and its descriptors."""
import math
import numpy as np
from scipy.spatial import HalfspaceIntersection, ConvexHull
from scipy.special import sph_harm_y


class Shape:
    def __init__(self, normals, dists, tags=None):
        A = np.asarray(normals, float)
        A = A / np.linalg.norm(A, axis=1)[:, None]
        b = np.asarray(dists, float)
        hs = HalfspaceIntersection(np.hstack([A, -b[:, None]]), np.zeros(3))
        self.V = hs.intersections
        self.hull = ConvexHull(self.V)
        self.tags = tags if tags is not None else [None] * len(A)
        self.A, self.b = A, b
        # which input planes actually carry a face, and their areas
        self.faces = []      # list of (tag, normal, polygon vertices, area)
        groups = {}
        for eq, simp in zip(self.hull.equations, self.hull.simplices):
            key = tuple(np.round(eq[:3], 6))
            groups.setdefault(key, []).append(simp)
        for key, simps in groups.items():
            n = np.array(key)
            idx = sorted(set(np.concatenate(simps)))
            P = self.V[idx]
            c = P.mean(0)
            u = P[0] - c; u /= np.linalg.norm(u); w = np.cross(n, u)
            P = P[np.argsort(np.arctan2((P - c) @ w, (P - c) @ u))]
            area = sum(0.5 * np.linalg.norm(np.cross(self.V[s[1]] - self.V[s[0]], self.V[s[2]] - self.V[s[0]]))
                       for s in simps)
            j = int(np.argmax(A @ n))
            self.faces.append(dict(tag=self.tags[j], normal=n, poly=P, area=area))

    # ---- descriptors -------------------------------------------------------
    @property
    def volume(self):
        return self.hull.volume

    @property
    def area(self):
        return self.hull.area

    def sphericity(self):
        return math.pi ** (1 / 3) * (6 * self.volume) ** (2 / 3) / self.area

    def gyration(self):
        """Exact gyration tensor of the solid polytope by tetrahedral decomposition."""
        c0 = self.V.mean(0)
        M = 0.0; first = np.zeros(3); second = np.zeros((3, 3))
        for s in self.hull.simplices:
            T = np.vstack([c0, self.V[s]])          # tetra vertices
            vol = abs(np.linalg.det(T[1:] - T[0])) / 6
            # second moment of a tetrahedron: vol/20 * (sum_i v_i v_i^T + (sum v)(sum v)^T)
            S = T.sum(0)
            second += vol / 20 * (T.T @ T + np.outer(S, S))
            first += vol * T.mean(0); M += vol
        com = first / M
        return second / M - np.outer(com, com)

    def kappa2(self):
        lam = np.linalg.eigvalsh(self.gyration())
        return float(1.5 * np.sum(lam ** 2) / np.sum(lam) ** 2 - 0.5)

    def aspect_ratio(self):
        lam = np.sort(np.linalg.eigvalsh(self.gyration()))
        return float(math.sqrt(lam[-1] / lam[0]))

    def q_l(self, l):
        """Steinhardt-type order parameter of the area-weighted face normals.
        Separates cube (Q4=0.764, Q6=0.354) from octahedron (Q4=0.509, Q6=0.629)."""
        w = np.array([f["area"] for f in self.faces]); w = w / w.sum()
        N = np.array([f["normal"] for f in self.faces])
        theta = np.arccos(np.clip(N[:, 2], -1, 1)); phi = np.arctan2(N[:, 1], N[:, 0])
        tot = 0.0
        for m in range(-l, l + 1):
            tot += abs(np.sum(w * sph_harm_y(l, m, theta, phi))) ** 2
        return float(math.sqrt(4 * math.pi / (2 * l + 1) * tot))

    def face_fractions(self):
        out = {}
        for f in self.faces:
            out[f["tag"]] = out.get(f["tag"], 0) + f["area"]
        tot = sum(out.values())
        return {k: v / tot for k, v in out.items()}

    def summary(self):
        return dict(n_faces=len(self.faces), n_vertices=len(self.V), sphericity=self.sphericity(),
                    kappa2=self.kappa2(), aspect_ratio=self.aspect_ratio(), Q3=self.q_l(3), Q4=self.q_l(4), Q6=self.q_l(6),
                    face_area_fraction=self.face_fractions())
