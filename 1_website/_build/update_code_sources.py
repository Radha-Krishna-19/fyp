#!/usr/bin/env python3
"""update_code_sources.py -- adds files to code_sources.js without touching
any entry already there.

WHY THIS EXISTS
code_sources.js says "Regenerated from the files on disk" but no generator
script for it was ever checked in -- it had been hand-assembled once, then
never updated as code_12 through code_18 (the convergence sweep, the
size-strata analysis, the topological-diversity check, the full-dataset
correct-graph band, and the ordering-equivalence proof) were added. Those
files were on disk and in git, but not in the in-page source browser
(code.html), so a reader clicking through the site's own "every line of
source code" page could not see the code that produced the site's
headline finding. This script closes that gap and is the generator the
comment always claimed existed, so it does not go stale the same way again.

Run:  python 1_website/_build/update_code_sources.py
Then: python 1_website/_build/build_site.py   (code.html embeds the .js file
      directly via a <script> tag, so no separate rebuild step touches its
      content -- but running build_site.py is still the house rule after any
      change under 1_website/.)
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WEBSITE = os.path.abspath(os.path.join(HERE, '..'))
PYDIR = os.path.abspath(os.path.join(WEBSITE, '..', '2_python'))
DATASET_SCALING = os.path.abspath(os.path.join(WEBSITE, '..', '9_dataset', 'size_scaling'))
OUT = os.path.join(WEBSITE, 'code_sources.js')

# filename -> (tag, one-line description). Only files NOT already embedded
# need an entry here; existing entries are left exactly as they are.
NEW_FILES = {
    # ---- the convergence / correct-band analysis modules ------------------
    'code_12_converged_band.py': ('OURS',
        'Coarse-grain the unit cell, replicate combinatorially; finite-size and q-range convergence sweep'),
    'code_13_scaling_regimes.py': ('OURS',
        'Tests directly whether the atomic graph has two scaling regimes (molecular vs framework)'),
    'code_14_size_strata.py': ('OURS',
        "Rebuilds the correct coarse-grained graph independently of a teammate's run; network stats per class"),
    'code_15_dataset_sweeps.py': ('OURS',
        'Capped Delta-alpha(D) slope sweep on both datasets -- does the divergence slope vary by framework?'),
    'code_16_topological_diversity.py': ('OURS',
        'Classifies structures by coordination signature; assembles a topologically diverse comparison set'),
    'code_17_full_correct_band.py': ('OURS',
        'The full, correct band: all 77 hMOF + all 61 CoRE MOF, on the coarse-grained supercell graph'),
    'code_18_subband_explain.py': ('OURS',
        'Sorts each dataset into Narrow/Medium/Wide and reports 9 comparison categories per class'),
    # ---- one-off scripts: fetch/run/plot drivers, kept for provenance -----
    '_ci_smoke_test.py': ('Verify',
        'The same coordination-number checks GitHub Actions runs on every push'),
    '_run_size_scaling.py': ('Verify',
        'Driver for the real finite-size + q-range convergence sweep behind fig13'),
    '_prove_ordering_equivalence.py': ('Verify',
        'Empirical proof: coarse-grain-then-replicate and atomic-then-coarse-grain give an identical graph'),
}

NEW_FIGURE_SCRIPTS = {
    'make_convergence_figure.py': ('Figure',
        'Draws the Delta-alpha vs ln(diameter) figure (fig13) from the convergence sweep'),
    'make_slope_figure.py': ('Figure',
        'Draws the Delta-alpha(D) slope comparison figure (fig14) across both datasets'),
    'make_full_band_figure.py': ('Figure',
        'Draws the full correct-band figures (fig15, fig16) from the complete-dataset run'),
    'make_grouped_spectra_figure.py': ('Figure',
        'Draws the grouped-spectra band figure (fig17): shaded mean +/- 1sd envelope per class'),
}


def lang_of(path):
    return 'python'


def load_existing():
    s = open(OUT, encoding='utf-8').read()
    start = s.index('{')
    end = s.rindex('}')
    header = s[:start]
    data = json.loads(s[start:end + 1])
    return header, data


def add_files(data, directory, mapping):
    added = []
    for fname, (tag, desc) in mapping.items():
        if fname in data:
            continue
        path = os.path.join(directory, fname)
        if not os.path.exists(path):
            print(f'  SKIP (not found): {fname}')
            continue
        src = open(path, encoding='utf-8').read()
        data[fname] = {'src': src, 'lang': lang_of(fname), 'tag': tag, 'desc': desc}
        added.append(fname)
    return added


def main():
    header, data = load_existing()
    print(f'{len(data)} files currently embedded')

    added = []
    added += add_files(data, PYDIR, NEW_FILES)
    added += add_files(data, DATASET_SCALING, NEW_FIGURE_SCRIPTS)

    print(f'added {len(added)}: {added}')

    body = json.dumps(data, indent=0, ensure_ascii=False)
    # json.dumps with indent=0 still puts each key on its own line but with
    # no leading spaces, matching the existing file's minimal-diff style.
    out = header + body + '\n'
    open(OUT, 'w', encoding='utf-8', newline='\n').write(out)
    print(f'wrote {OUT} ({len(data)} files total)')


if __name__ == '__main__':
    main()
