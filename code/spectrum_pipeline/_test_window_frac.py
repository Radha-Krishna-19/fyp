"""
Does a WINDOW_FRAC=0.50 radius cap (fit tau(q) over radii
1..round(0.5*diameter) instead of the full 1..diameter) converge with
supercell size, where the full-diameter version does not?

This is a genuinely different question from the graph-ordering one already
settled in _prove_ordering_equivalence.py (that question is closed: the
graph is identical either way). This script asks about a SEPARATE parameter
in the SPECTRUM-FITTING step: how much of the radius range to include in the
tau(q) fit. Both the half-diameter and full-diameter caps are legitimate
choices to test, not a bug in either.
"""
from __future__ import annotations
import numpy as np
from code_12_converged_band import (quotient_graph_from_cif, replicate,
                                     select_influential, fast_diameter,
                                     probability_measures, compute_tau)


def spectrum_windowed(G, influential, window_frac, q_values=None, n_trials=20,
                       seed=0, diameter=None):
    """Same as code_12.spectrum(), except radii are capped at
    round(window_frac * diameter) -- her exact rule, including her diam-1
    ceiling."""
    if q_values is None:
        q_values = np.linspace(-10, 10, 41)
    if diameter is None:
        diameter = fast_diameter(G)
    if diameter < 8:
        return {'ok': False, 'reason': f'diameter {diameter} too small'}

    rmax = max(3, int(round(diameter * window_frac)))
    rmax = min(rmax, max(2, diameter - 1))          # her ceiling
    radii = list(range(1, rmax + 1))

    trials = probability_measures(G, influential, radii, n_trials=n_trials, seed=seed)
    tau, r2 = compute_tau(trials, radii, diameter, q_values)
    alpha = np.gradient(tau, q_values)
    finite = np.isfinite(alpha)
    if not finite.any():
        return {'ok': False, 'reason': 'no finite alpha'}
    width = float(np.nanmax(alpha) - np.nanmin(alpha))
    return {'ok': True, 'width': width, 'diameter': diameter, 'rmax': rmax,
            'r2_linearity_mean': float(np.nanmean(r2))}


def sweep(cif_path, window_frac, n_values=(2, 3, 4, 6, 8), n_trials=20, n_seeds=3,
          max_nodes=25000, influential_frac=0.20):
    blocks, edges, _geom = quotient_graph_from_cif(cif_path)
    K = len(blocks)
    out = []
    for n in n_values:
        if K * n ** 3 > max_nodes:
            break
        G, _kind = replicate(blocks, edges, n)
        infl, _sel = select_influential(G, top_percent=influential_frac)
        diam = fast_diameter(G)
        widths = []
        for s in range(n_seeds):
            r = spectrum_windowed(G, infl, window_frac, n_trials=n_trials,
                                   seed=s * 101, diameter=diam)
            if r.get('ok'):
                widths.append(r['width'])
        if not widths:
            continue
        out.append({'n': n, 'cg_nodes': G.number_of_nodes(), 'diameter': diam,
                    'width_mean': float(np.mean(widths)), 'width_sd': float(np.std(widths))})
    return out


if __name__ == '__main__':
    nets = {'HKUST-1.cif': 'tbo', 'MOF5.cif': 'pcu', 'ZIF-8.cif': 'sod', 'UiO-66.cif': 'fcu'}
    print(f"{'structure':<10}{'net':<5}{'n':<4}{'CG-N':<8}{'diam':<6}{'rmax(0.5*diam)':<16}"
          f"{'width (full)':<14}{'width (0.5-cap)':<16}")
    for cif, net in nets.items():
        full = sweep(cif, window_frac=1.0)     # her rule with window_frac=1.0 == full diameter
        half = sweep(cif, window_frac=0.50)     # her actual rule
        for rf, rh in zip(full, half):
            print(f"{cif.replace('.cif',''):<10}{net:<5}{rf['n']:<4}{rf['cg_nodes']:<8}"
                  f"{rf['diameter']:<6}{'~'+str(max(3,round(rf['diameter']*0.5))):<16}"
                  f"{rf['width_mean']:<14.4f}{rh['width_mean']:<16.4f}")

        # fit slope of width vs ln(diameter) under each window rule
        d_full = np.array([r['diameter'] for r in full], dtype=float)
        w_full = np.array([r['width_mean'] for r in full])
        d_half = np.array([r['diameter'] for r in half], dtype=float)
        w_half = np.array([r['width_mean'] for r in half])
        if len(d_full) >= 3:
            s_full = np.polyfit(np.log(d_full), w_full, 1)[0]
            s_half = np.polyfit(np.log(d_half), w_half, 1)[0]
            drift_full = abs(w_full[-1] - w_full[-2]) / w_full[-1]
            drift_half = abs(w_half[-1] - w_half[-2]) / w_half[-1]
            print(f"  -> slope vs ln(D): full-diameter={s_full:+.3f}, half-diameter-cap={s_half:+.3f}")
            print(f"  -> drift at largest step: full-diameter={drift_full:.3f}, half-diameter-cap={drift_half:.3f}")
        print()
