"""CHGNet surface energies -> Wulff shape -> comparison with laboratory crystal shapes.

Everything about the MOFs and the experiments comes from input files; nothing about any
particular MOF is written into this code.

INPUTS
  mofs.csv   one row per MOF.  Required columns: mof, cif
             Optional columns: faces   (e.g. "100 110 111"; default --faces)
                               symprec (symmetry tolerance in A; default --symprec)
             'cif' is a path, absolute or relative to the CSV's folder.
  lab.csv    laboratory shapes. Two layouts are accepted:
             (a) the project dataset experimental_morphology.csv (columns mof, morphology,
                 additive, source_id, ...): rows with no additive are taken as the
                 benchmark and the most frequent shape per MOF is the lab shape;
             (b) a simple table with columns mof, shape (optional: facet, source).
             MOF names are matched ignoring case, spaces, hyphens and underscores.

METHOD (see blockslab.py and capping.py)
  * Slabs are built from whole building blocks (metal clusters and linkers), so only
    metal-linker bonds are cut and every slab is stoichiometric.
  * gamma = (E_slab - N * e_bulk) / (2 A), CHGNet energies, atoms relaxed at fixed cell.
    For slabs whose two faces differ this is the average of the two faces
    (basis = 'asymmetric_average').
  * Optional --cap water heals every broken metal-ligand bond with one H2O.
  * Lowest gamma per face family -> pymatgen WulffShape -> area fractions -> shape name.

OUTPUTS (in --out)
  slabs.csv              every slab computed (energy, gamma, steps, convergence, ...)
  surface_energies.csv   lowest gamma per MOF and face, the values used for Wulff
  wulff_summary.csv      predicted shape, area fractions, lab shape, match flags
  cache/<MOF>/*.json     per-slab cache; rerunning only computes what is missing

USAGE
  python chgnet_wulff.py --mofs mofs.csv --lab experimental_morphology.csv --out results
  python chgnet_wulff.py --mofs mofs.csv --lab lab.csv --out results --static        # quick test
  python chgnet_wulff.py --mofs mofs.csv --lab lab.csv --out results --only MOF-5    # one MOF
  python chgnet_wulff.py --mofs mofs.csv --lab lab.csv --out results --report-only
"""
import argparse
import hashlib
import json
import re
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
EV_A2_TO_J_M2 = 16.0218

# Vocabulary only (not data): which face family bounds each named cubic polyhedron, and
# synonyms used in papers. Used to read the lab table and to name predicted shapes.
SHAPE_FACET = {"cube": "{100}", "truncated_cube": "{100}", "octahedron": "{111}",
               "truncated_octahedron": "{111}", "rhombic_dodecahedron": "{110}",
               "truncated_rhombic_dodecahedron": "{110}", "cuboctahedron": "{100}+{111}"}
SYNONYMS = {"bipyramid": "octahedron", "square_bipyramid": "octahedron",
            "rhombic dodecahedron": "rhombic_dodecahedron", "cubic": "cube",
            "octahedral": "octahedron"}
NO_ADDITIVE = {"", "none", "nan", "no", "no additive", "-"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def norm_name(s):
    return re.sub(r"[\s\-_()]", "", str(s)).lower()


def parse_faces(text):
    """'100 110 111' or '100;1-11' -> [(1,0,0), ...]; 'm' or '-' marks a minus sign."""
    out = []
    for tok in re.split(r"[;,\s]+", str(text).strip()):
        if not tok:
            continue
        tok = tok.replace("m", "-")
        digits = re.findall(r"-?\d", tok)
        if len(digits) != 3:
            raise ValueError(f"cannot read face {tok!r}; write it like 100 or 1-11")
        out.append(tuple(int(d) for d in digits))
    return out


# --------------------------------------------------------------------------- lab table
def read_lab(path):
    """Return {normalised mof name: dict(shape, facet, n_records, shape_counts, sources)}."""
    if not path:
        return {}
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    out = {}
    if "morphology" in cols:                      # project dataset layout
        add = df[cols["additive"]].astype(str).str.strip().str.lower() if "additive" in cols else ""
        df = df[add.isin(NO_ADDITIVE)] if "additive" in cols else df
        for mof, g in df.groupby(cols["mof"]):
            shapes = [SYNONYMS.get(str(s).lower(), str(s).lower()) for s in g[cols["morphology"]]]
            polyhedra = [s for s in shapes if s in SHAPE_FACET]
            if not polyhedra:
                continue
            cnt = Counter(polyhedra)
            top = cnt.most_common()
            src = sorted(set(g[cols["source_id"]].astype(str))) if "source_id" in cols else []
            if len(top) > 1 and top[0][1] == top[1][1]:      # tie: do not pick one silently
                tied = [s for s, n in top if n == top[0][1]]
                out[norm_name(mof)] = {"lab_shape": "ambiguous:" + "/".join(tied),
                                       "lab_facet": "+".join(SHAPE_FACET[s] for s in tied),
                                       "lab_n_records": len(polyhedra),
                                       "lab_shape_counts": dict(cnt), "lab_sources": " ".join(src)}
                continue
            shape = top[0][0]
            out[norm_name(mof)] = {"lab_shape": shape, "lab_facet": SHAPE_FACET[shape],
                                   "lab_n_records": len(polyhedra),
                                   "lab_shape_counts": dict(cnt), "lab_sources": " ".join(src)}
    elif "shape" in cols:                         # simple layout
        for _, r in df.iterrows():
            shape = SYNONYMS.get(str(r[cols["shape"]]).lower().strip(),
                                 str(r[cols["shape"]]).lower().strip().replace(" ", "_"))
            facet = r[cols["facet"]] if "facet" in cols and pd.notna(r[cols["facet"]]) \
                else SHAPE_FACET.get(shape, "")
            out[norm_name(r[cols["mof"]])] = {
                "lab_shape": shape, "lab_facet": facet, "lab_n_records": 1,
                "lab_shape_counts": {shape: 1},
                "lab_sources": str(r[cols["source"]]) if "source" in cols else ""}
    else:
        raise ValueError(f"{path}: need a 'morphology' column (dataset layout) or a 'shape' column")
    return out


# --------------------------------------------------------------------------- CHGNet
def load_conventional(cif, symprec):
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    s = Structure.from_file(cif)
    sga = SpacegroupAnalyzer(s, symprec=symprec)
    return s, sga.get_conventional_standard_structure(), sga.get_primitive_standard_structure(), \
        sga.get_space_group_symbol()


def chgnet_model():
    from chgnet.model import CHGNet
    return CHGNet.load(verbose=False)


def energy(model, struct, relax_steps, fmax):
    """Total energy (eV); atoms relaxed at fixed cell when relax_steps > 0."""
    from chgnet.model import StructOptimizer
    if relax_steps <= 0:
        pred = model.predict_structure(struct, task="e")
        return float(pred["e"]) * len(struct), struct, 0, None
    res = StructOptimizer(model=model).relax(struct, fmax=fmax, steps=relax_steps,
                                             relax_cell=False, verbose=False)
    traj = res["trajectory"]
    return (float(traj.energies[-1]), res["final_structure"], len(traj.energies),
            float(np.abs(np.array(traj.forces[-1])).max()))


class Cache:
    def __init__(self, root, mof):
        self.dir = Path(root) / "cache" / re.sub(r"[^\w.-]", "_", mof)
        self.dir.mkdir(parents=True, exist_ok=True)

    def get(self, key):
        p = self.dir / f"{key}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def put(self, key, rec):
        (self.dir / f"{key}.json").write_text(json.dumps(rec, indent=1, default=str))

    def all_slabs(self):
        return [json.loads(p.read_text()) for p in self.dir.glob("slab_*.json")]


def run_mof(model, mof, cif, faces, symprec, a, cache):
    from blockslab import block_slabs, is_mirror_symmetric
    from capping import cap_with_water, water_energy
    raw, conv, prim, sg = load_conventional(cif, symprec)
    log(f"{mof}: {len(raw)} atoms in CIF, space group {sg}, conventional {len(conv)}, primitive {len(prim)}")
    cache.put("meta", {"mof": mof, "cif": str(cif), "space_group": sg,
                       "conv_lattice": conv.lattice.matrix.tolist(), "symprec": symprec})
    bkey = f"bulk_r{a.relax_steps}"
    bulk = cache.get(bkey)
    if bulk is None:
        t = time.time()
        e, _, n, fm = energy(model, prim, a.relax_steps, a.fmax)
        bulk = {"n_atoms": len(prim), "energy_eV": e, "e_per_atom_eV": e / len(prim),
                "steps": n, "final_fmax": fm, "seconds": round(time.time() - t, 1)}
        cache.put(bkey, bulk)
    e_bulk = bulk["e_per_atom_eV"]
    e_water = 0.0
    if a.cap == "water":
        w = cache.get("water")
        if w is None:
            w = {"E_H2O_eV": water_energy(model)}
            cache.put("water", w)
        e_water = w["E_H2O_eV"]
    log(f"   bulk {e_bulk:.4f} eV/atom" + (f", E(H2O) {e_water:.4f} eV" if a.cap == "water" else ""))
    for hkl in faces:
        made = block_slabs(conv, prim, hkl, a.thickness, a.vacuum)
        log(f"   {hkl}: {len(made)} block terminations, computing up to {a.max_terms}")
        for i, m in enumerate(made[: a.max_terms]):
            sl = m["slab"]
            sig = hashlib.md5(sl.to(fmt="poscar").encode()).hexdigest()[:8]
            key = f"slab_{''.join(map(str, hkl)).replace('-', 'm')}_t{i}_{sig}_r{a.relax_steps}_{a.cap}"
            if cache.get(key):
                log(f"      t{i}: cached gamma {cache.get(key)['gamma_J_m2']:.3f} J/m2")
                continue
            A = float(np.linalg.norm(np.cross(sl.lattice.matrix[0], sl.lattice.matrix[1])))
            capped, n_water, info = cap_with_water(sl, conv)
            intact = info["status"] in ("capped", "nothing_to_cap")
            work = sl
            if a.cap == "water":
                if capped is None:
                    log(f"      t{i}: cannot cap ({info['status']}), skipped")
                    continue
                work = capped
            else:
                n_water = 0
            sym = is_mirror_symmetric(sl)
            t = time.time()
            e, final, n, fm = energy(model, work, a.relax_steps, a.fmax)
            gamma = (e - len(sl) * e_bulk - n_water * e_water) / (2 * A) * EV_A2_TO_J_M2
            rec = {"mof": mof, "h": hkl[0], "k": hkl[1], "l": hkl[2],
                   "face": "{" + "".join(map(str, hkl)) + "}", "termination": i,
                   "z0_A": m["z0"], "n_layers": m["n_layers"], "thickness_A": m["thickness_A"],
                   "n_atoms": len(work), "area_A2": round(A, 3), "symmetric": sym,
                   "basis": "exact" if sym else "asymmetric_average",
                   "blocks_intact": intact, "broken_metal_ligand_bonds": info["missing_metal_bonds"],
                   "cap": a.cap, "n_water": n_water, "relax_steps": a.relax_steps,
                   "steps_taken": n, "final_fmax": fm,
                   "converged": fm is None or fm <= a.fmax + 1e-9,
                   "energy_eV": e, "gamma_J_m2": round(gamma, 5),
                   "seconds": round(time.time() - t, 1)}
            cache.put(key, rec)
            if a.save_slabs:
                final.to(filename=str(cache.dir / f"{key}.cif"))
            log(f"      t{i}: {len(work)} atoms, gamma {gamma:.3f} J/m2, {rec['seconds']} s, "
                f"{n} steps, converged {rec['converged']}")


# --------------------------------------------------------------------------- Wulff
def name_shape(frac):
    f = lambda k: frac.get(k, 0.0)
    if f("{100}") > 0.95: return "cube"
    if f("{111}") > 0.95: return "octahedron"
    if f("{110}") > 0.95: return "rhombic_dodecahedron"
    top = max(frac, key=frac.get)
    if top == "{111}" and f("{100}") > 0.05: return "truncated_octahedron"
    if top == "{100}" and f("{111}") > 0.05: return "truncated_cube"
    if top == "{110}": return "truncated_rhombic_dodecahedron"
    return f"mixed_dominant_{top}"


def summarise(out_dir, mofs, lab, a):
    from pymatgen.analysis.wulff import WulffShape
    from pymatgen.core import Lattice
    all_slabs, chosen, summary = [], [], []
    for mof in mofs:
        cache = Cache(out_dir, mof)
        meta = cache.get("meta")
        slabs = [r for r in cache.all_slabs()
                 if r["relax_steps"] == a.relax_steps and r["cap"] == a.cap]
        all_slabs += slabs
        ok = [r for r in slabs if r["blocks_intact"] and (a.relax_steps == 0 or r["converged"])]
        best = {}
        for r in ok:
            k = (r["h"], r["k"], r["l"])
            if k not in best or r["gamma_J_m2"] < best[k]["gamma_J_m2"]:
                best[k] = r
        chosen += list(best.values())
        row = {"mof": mof, "relax_steps": a.relax_steps, "cap": a.cap,
               "n_slabs": len(slabs), "n_used": len(ok)}
        for k, r in best.items():
            row[f"gamma_{''.join(map(str, k))}_J_m2"] = r["gamma_J_m2"]
        if meta and len(best) >= 2:
            ws = WulffShape(Lattice(meta["conv_lattice"]), list(best),
                            [best[k]["gamma_J_m2"] for k in best])
            frac = {}
            for mi, v in ws.area_fraction_dict.items():
                fam = "{" + "".join(map(str, sorted(np.abs(mi), reverse=True))) + "}"
                frac[fam] = frac.get(fam, 0.0) + v
            frac = {k: round(v, 3) for k, v in sorted(frac.items(), key=lambda kv: -kv[1]) if v > 1e-3}
            row.update({"predicted_shape": name_shape(frac), "dominant_face": max(frac, key=frac.get),
                        "area_fractions": json.dumps(frac), "shape_factor": round(ws.shape_factor, 3)})
        else:
            row["predicted_shape"] = "not enough faces"
        L = lab.get(norm_name(mof), {})
        row.update({k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in L.items()})
        if L and "dominant_face" in row:
            row["shape_match"] = row["predicted_shape"] == L["lab_shape"]
            row["dominant_face_match"] = row["dominant_face"] in L["lab_facet"]
        summary.append(row)
    out = Path(out_dir)
    pd.DataFrame(all_slabs).to_csv(out / "slabs.csv", index=False)
    pd.DataFrame(chosen).to_csv(out / "surface_energies.csv", index=False)
    sm = pd.DataFrame(summary)
    sm.to_csv(out / "wulff_summary.csv", index=False)
    return sm


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mofs", required=True, help="CSV with columns mof, cif [, faces, symprec]")
    ap.add_argument("--lab", default=None, help="lab shapes CSV (dataset or simple layout)")
    ap.add_argument("--out", default="results")
    ap.add_argument("--only", nargs="*", help="run only these MOF names from mofs.csv")
    ap.add_argument("--faces", default="100 110 111", help="default faces when the CSV has none")
    ap.add_argument("--max-terms", type=int, default=3, help="terminations per face")
    ap.add_argument("--thickness", type=float, default=15.0, help="minimum slab thickness, A")
    ap.add_argument("--vacuum", type=float, default=15.0)
    ap.add_argument("--symprec", type=float, default=0.1)
    ap.add_argument("--relax-steps", type=int, default=600, help="0 = static energies")
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--static", action="store_true", help="quick test: no relaxation")
    ap.add_argument("--cap", default="none", choices=["none", "water"])
    ap.add_argument("--save-slabs", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args(argv)
    if a.static:
        a.relax_steps = 0
    mofs_path = Path(a.mofs)
    table = pd.read_csv(mofs_path)
    table.columns = [c.strip().lower() for c in table.columns]
    missing = {"mof", "cif"} - set(table.columns)
    if missing:
        sys.exit(f"{mofs_path}: missing column(s) {sorted(missing)}")
    if a.only:
        want = {norm_name(x) for x in a.only}
        table = table[table["mof"].map(norm_name).isin(want)]
    lab = read_lab(a.lab)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if not a.report_only:
        model = chgnet_model()
        for _, r in table.iterrows():
            cif = Path(str(r["cif"]))
            if not cif.is_absolute():
                cif = mofs_path.parent / cif
            if not cif.exists():
                log(f"{r['mof']}: CIF not found at {cif}, skipped")
                continue
            faces = parse_faces(r["faces"]) if "faces" in table and pd.notna(r.get("faces")) \
                else parse_faces(a.faces)
            sp = float(r["symprec"]) if "symprec" in table and pd.notna(r.get("symprec")) else a.symprec
            try:
                run_mof(model, str(r["mof"]), str(cif), faces, sp, a, Cache(a.out, str(r["mof"])))
            except Exception as exc:
                log(f"{r['mof']}: FAILED {type(exc).__name__}: {exc}")
    sm = summarise(a.out, list(table["mof"].astype(str)), lab, a)
    cols = [c for c in ["mof", "predicted_shape", "dominant_face", "area_fractions", "lab_shape",
                        "lab_n_records", "shape_match", "dominant_face_match"] if c in sm.columns]
    print(sm[cols].to_string(index=False))
    return sm


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
