#!/usr/bin/env python3
"""
build_site.py — splits the original single-page site into a multi-page
documentation portal, without changing a byte of the section content.

WHY A SCRIPT AND NOT HAND-EDITING
The source page carries ~95 KB of reviewed technical prose across 19
sections. Re-typing it into eight files is how content gets silently lost or
subtly altered. This script slices at the <h2> boundaries and re-emits the
slices verbatim, so the only things that change are the shell around them,
the per-page section numbering, and cross-page link targets. The assertions
at the end verify that every section survived and that no anchor dangles.

Run:  python3 _build/build_site.py     (from anywhere)
"""
import re, os, sys, json, html

# Paths are resolved relative to THIS file, not the shell's working directory,
# so the build works from anywhere.
HERE  = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)            # figure_sources.py lives beside this script
SRC   = os.path.join(HERE, 'content_source.html')   # all 19 sections, one file
OUT   = os.path.abspath(os.path.join(HERE, '..'))   # the served folder
FRAG  = os.path.join(HERE, 'fragments')

# ---------------------------------------------------------------------------
# PAGE PLAN
# Sections are grouped by the question a reader is asking, not by the order
# they were written in. `network_page.js` drives both the network and the
# spectrum sections, so those two pages both load it.
# ---------------------------------------------------------------------------
PAGES = [
    dict(file='index.html',        nav='Overview',      sections=['problem', 'question'],
         title='Overview',
         desc='What a metal-organic framework is, the question this project asks, and the honest answer so far.'),

    dict(file='journey.html',      nav='How We Got Here', sections=[],
         title='How We Got Here: The Whole Project in Order',
         desc='From the papers we read to where the project is now: what was built from each, which code and notebooks produced which results, every mistake and its correction, and why each method was chosen over the alternatives.'),

    dict(file='methodology.html',  nav='Methodology',   sections=['why', 'parts', 'implementation', 'roadmap'],
         title='Methodology and Architecture',
         desc='The full workflow, the system architecture, the datasets, the evaluation strategy, and the justification for each choice.'),

    dict(file='decomposition.html', nav='Decomposition', sections=['walkthrough'],
         title='The Decomposition Algorithm',
         desc='The published metal-oxo decomposition, module by module, with the real code beside a live 3D model.'),

    dict(file='network.html',      nav='Network',       sections=['primer', 'graph', 'influence', 'defect', 'fingerprint'],
         title='From Crystal to Network',
         desc='Every graph-theory term defined from scratch, the periodic quotient graph, centrality, defects, and the Laplacian spectrum.'),

    dict(file='spectrum.html',     nav='Spectrum',      sections=['paper-use', 'multifractal', 'paper'],
         title='The Multifractal Spectrum',
         desc='What the parabola on every chart here actually means, the published method we build on, the mathematics, and all 61 real spectra as computed.'),

    dict(file='results.html',      nav='Results',       sections=['band', 'reproduce-band'],
         title='Results: The Band',
         desc='The multifractal band across 77 frameworks, the size confound that killed the pore-size claim, and what survives.'),

    dict(file='learn_shape.html',  nav='Learn',         sections=[],
         title='Learn: Crystals and Their Shapes',
         desc='Everything needed to follow the morphology work, from scratch and with a picture for each idea: unit cells, Miller planes, symmetry, how crystals grow, shape rules, measuring shape, and periodic graphs.'),

    dict(file='learn_energy.html', nav='Learn 2',      sections=[],
         title='Learn: Energies, Statistics and Tools',
         desc='Just enough, from scratch, to follow the rest of the project: surface and cleavage energy, slabs and terminations, where energies come from (force field, CHGNet, DFT), combining two shape methods, the statistics used, finite particles, and the software tools.'),

    dict(file='morph_math.html',   nav='Maths',         sections=[],
         title='Phase 2: The Mathematics of Crystal Shape',
         desc='Every rule used by the morphology work stated as a proposition and proved, with each proposition checked numerically in your browser.'),

    dict(file='cif_to_shape.html', nav='CIF to Shape',  sections=[],
         title='From a CIF File to a Crystal Shape',
         desc='Every step from the numbers in a CIF file to the crystal shape, computed in your browser with the full working shown: lattice, metric tensor, centring and point group found from the atoms, structure factors, face spacings, the BFDH rule, the shape built plane by plane, and the map of every shape a cubic crystal can take.'),

    dict(file='morphology.html',   nav='Morphology',    sections=[],
         title='Morphology: Crystal Shapes from the Unit Cell',
         desc='The panel\'s second question: from one established unit cell, generate several crystal morphologies, mathematically and computationally. Method, live shape explorer, results for four MOFs, and the comparison with experiment.'),

    dict(file='deform.html',       nav='Cell Deform',   sections=[],
         title='Changing the Unit Cell: Plates, Crystals and Rods',
         desc='The second reading of the panel\'s question: change the unit-cell parameters of an established MOF and see which shapes follow, with the exact rules and a live explorer.'),

    dict(file='graph_faces.html',  nav='Graph Faces',   sections=[],
         title='Phase 3: Crystal Faces from the Periodic Graph',
         desc='Which faces are flat, how fast each grows, and which shape results, computed from each framework\'s own periodic graph and compared with experiment.'),

    dict(file='surface_energy.html', nav='Surface Energy', sections=[],
         title='Phase 4: Surface Energies from a Force Field',
         desc='Cleavage energy of every crystal face computed from the atoms of each framework with a force field, the Wulff shapes that follow, and how robust they are.'),

    dict(file='hybrid.html',       nav='Hybrid',        sections=[],
         title='Combining BFDH and Wulff',
         desc='One rule that blends the geometric (BFDH) and energetic (Wulff) shape methods, what it gives for four MOFs, why no best weight is claimed, and the notebook that runs it on any crystal file.'),

    dict(file='experiment.html',   nav='Experiment',    sections=[],
         title='Experiment, CHGNet and Every Method Compared',
         desc='Real crystals of these MOFs and the conditions they were grown under, the machine-learned (CHGNet) surface energies, the chemistry problems found in the slabs, every shape method scored against experiment, and the pipeline run on CoRE MOF structures.'),

    dict(file='bridge.html',       nav='Why Shape', sections=[],
         title='Why Shape Matters, and How the Two Halves Connect',
         desc='Why the project changes the shape of MOFs, how the earlier spectrum-based classification relates to morphology, a new test of whether the spectrum sees particle shape, and how the first half can be reused.'),

    dict(file='relation.html',     nav='Spectrum ↔ Shape', sections=[],
         title='Spectrum and Crystal Shape: Testing the Relation',
         desc='Four calculations that test whether the spectrum width of the first half of the project, and the related mass-radius dimension profile, carry information about the crystal shapes predicted in the second half.'),

    dict(file='lessons.html',      nav='Mistakes',      sections=[],
         title='What We Got Wrong and How We Fixed It',
         desc='Every mistake made so far, in plain words and in technical words: what we did, why we chose it, why it was wrong, and what we did to fix it.'),

    dict(file='code.html',         nav='Source',        sections=['source'],
         title='Every Line of Source Code',
         desc='Every source file of the project, readable in the browser with no download and no web server.'),

    dict(file='resources.html',    nav='Resources',     sections=[],
         title='Resources: Paper, Reports, Notebooks and Data',
         desc='The team paper, the reports and slides, every notebook (in the repository and in Google Colab), the datasets, the certifications and a map of the repository.'),

    dict(file='references.html',   nav='References',    sections=['references'],
         title='References',
         desc='Every paper, dataset and tool this project builds on.'),

    dict(file='glossary.html',     nav='Glossary',      sections=[],
         title='Glossary',
         desc='Every term and symbol used anywhere on this site, defined from first principles and ordered so each one only depends on earlier ones.'),

    dict(file='team.html',         nav='Team',          sections=[],
         title='Team, Progress and Deliverables',
         desc='Who did what, how far the implementation has actually got, and where every deliverable lives.'),
]

# Which engine scripts each page needs. Loading only what a page uses keeps
# code_sources.js (a large embedded source bundle) off the seven pages that
# do not have a code browser on them.
SCRIPTS = {
    'index.html':         ['default_cif_data.js', 'mof_decompose.js', 'mof_network.js', 'overview_page.js'],
    'journey.html':       [],
    'methodology.html':   ['default_cif_data.js', 'mof_decompose.js', 'mof_network.js', 'overview_page.js'],
    'decomposition.html': ['THREE', 'mof_decompose.js', 'mof_render.js', 'mof_stages.js', 'mof_controls.js',
                           'default_cif_data.js', 'pipeline_walkthrough.js', 'app.js'],
    'network.html':       ['THREE', 'mof_decompose.js', 'mof_render.js', 'mof_network.js',
                           'mof_multifractal.js', 'default_cif_data.js', 'network_page.js'],
    'spectrum.html':      ['mof_decompose.js', 'mof_network.js', 'mof_multifractal.js',
                           'default_cif_data.js', 'network_page.js'],
    'results.html':       ['band_data.js', 'band_page.js',
                           'real_band_data.js', 'real_band_page.js'],
    'learn_shape.html':   [],
    'learn_energy.html':  [],
    'morph_math.html':    ['mof_morphology.js', 'mof_deform.js', 'morph_math_page.js'],
    'cif_to_shape.html':  ['default_cif_data.js', 'mof_morphology.js', 'mof_cif_shape.js', 'cif_shape_data.js', 'cif_shape_page.js'],
    'morphology.html':    ['mof_morphology.js', 'morphology_page.js'],
    'deform.html':        ['mof_morphology.js', 'mof_deform.js', 'deform_page.js'],
    'graph_faces.html':   ['phase3_data.js', 'graph_faces_page.js'],
    'surface_energy.html': [],
    'hybrid.html':        [],
    'experiment.html':    [],
    'bridge.html':        [],
    'relation.html':      [],
    'lessons.html':       [],
    'code.html':          ['code_sources.js', 'code_viewer.js', 'single_page.js'],
    'resources.html':     [],
    'references.html':    [],
    'glossary.html':      [],
    'team.html':          [],
}

# The contents rail groups the pages into the parts a reader moves through. Each entry is
# (file, label in the rail). The labels are longer and plainer than the old one-word menu.
PARTS = [
    ('Start', [('index.html', 'Overview'), ('journey.html', 'How we got here'),
               ('methodology.html', 'Methodology')]),
    ('Part I. Graphs and the spectrum', [('decomposition.html', 'Decomposition'),
               ('network.html', 'From crystal to network'), ('spectrum.html', 'The multifractal spectrum'),
               ('results.html', 'Results: the band')]),
    ('Part II. Crystal shape', [('learn_shape.html', 'Learn: crystal shapes'),
               ('learn_energy.html', 'Learn: surface energy'), ('morph_math.html', 'The mathematics'),
               ('cif_to_shape.html', 'From a CIF to a shape'), ('morphology.html', 'Morphology'),
               ('deform.html', 'Changing the cell'), ('graph_faces.html', 'Faces from the graph'),
               ('surface_energy.html', 'Surface energy'), ('hybrid.html', 'Blending BFDH and Wulff'),
               ('experiment.html', 'Against experiment')]),
    ('Connecting the two parts', [('bridge.html', 'Why shape'), ('relation.html', 'Spectrum and shape')]),
    ('Reference', [('lessons.html', 'Mistakes and fixes'), ('code.html', 'Source code'),
               ('resources.html', 'Resources'), ('references.html', 'References'),
               ('glossary.html', 'Glossary'), ('team.html', 'Team and progress')]),
]
# Pages outside the numbered reading sequence.
REFERENCE = ('lessons.html', 'code.html', 'resources.html', 'references.html', 'glossary.html', 'team.html')


# Short labels used when a cross-page link's visible text said "Section 7".
LABELS = {
    'problem': 'the problem', 'question': 'the question', 'why': 'why this path',
    'parts': 'what we built', 'implementation': 'the implementation map',
    'roadmap': 'the roadmap', 'walkthrough': 'the pipeline walkthrough',
    'primer': 'the graph primer', 'graph': 'building the network',
    'influence': 'influential blocks', 'defect': 'defects',
    'fingerprint': 'the Laplacian fingerprint', 'multifractal': 'the spectrum',
    'paper': 'box-growing', 'band': 'the band', 'reproduce-band': 'reproducing the band',
    'realband': 'the synthesised-MOF comparison', 'references': 'the references',
    'source': 'the source code',
}


def slice_sections(src):
    """Cut the source page into {id: html} at the <h2> boundaries."""
    body = src[src.index('<body>'):]
    pat = re.compile(r'<h2 class="(?:st|section-title)" id="([a-z-]+)">')
    marks = list(pat.finditer(body))
    if not marks:
        sys.exit('no sections found — has the source markup changed?')
    end = body.index('  <footer>') if '  <footer>' in body else len(body)
    out = {}
    for i, m in enumerate(marks):
        stop = marks[i + 1].start() if i + 1 < len(marks) else end
        out[m.group(1)] = body[m.start():stop].rstrip() + '\n'
    return out


def renumber(chunk, n):
    """Rewrite the section's display number for its position on the new page."""
    chunk = re.sub(r'(<span class="stitle-num">)\d+(</span>)', rf'\g<1>{n}\g<2>', chunk, count=1)
    chunk = re.sub(r'(<span class="n">)\d+(</span>)',          rf'\g<1>{n}\g<2>', chunk, count=1)
    return chunk


def fix_links(chunk, home, where):
    """Point every anchor at the page that now owns its target."""
    def repl(m):
        tid, attrs, text = m.group(1), m.group(2), m.group(3)
        if tid not in where:
            return m.group(0)                       # unknown id — leave untouched
        page = where[tid]
        href = f'#{tid}' if page == home else f'{page}#{tid}'
        # "Section 7" was a number into the old single page and is now wrong.
        if re.fullmatch(r'\s*Section\s+\d+\s*', re.sub(r'<[^>]+>', '', text)):
            text = LABELS.get(tid, text)
        return f'<a href="{href}"{attrs}>{text}</a>'
    return re.sub(r'<a href="#([a-z-]+)"([^>]*)>(.*?)</a>', repl, chunk, flags=re.S)


THEME_INIT = (
    '<script>(function(){try{var t=localStorage.getItem("mof-theme");'
    'if(!t)t="light";'
    'document.documentElement.setAttribute("data-theme",t);}catch(e){}})();</script>'
)


def script_tags(names):
    out = []
    for n in names:
        if n == 'THREE':
            # Local copy first so a fresh clone works with no network at all;
            # the CDN is only a fallback if the vendored file is missing.
            out.append('<script src="three.min.js"></script>\n'
                       '<script>if(!window.THREE){document.write('
                       '\'<script src="https:\\/\\/cdnjs.cloudflare.com\\/ajax\\/libs\\/three.js'
                       '\\/r128\\/three.min.js"><\\/script>\');}</script>')
        else:
            out.append(f'<script src="{n}"></script>')
    return '\n'.join(out)


def sidebar(page):
    """The contents rail: every page, grouped into parts, the reading steps numbered."""
    steps = [p['file'] for p in PAGES if p['file'] not in REFERENCE]
    files = [f for _, items in PARTS for f, _ in items]
    assert sorted(files) == sorted(p['file'] for p in PAGES), 'PARTS must list every page exactly once'
    out = []
    for part, items in PARTS:
        lis = []
        for f, label in items:
            cur = ' aria-current="page"' if f == page['file'] else ''
            num = f'<span class="nav-n">{steps.index(f) + 1}</span>' if f in steps else '<span class="nav-n"></span>'
            lis.append(f'        <li><a href="{f}"{cur}>{num}<span class="nav-t">{label}</span></a></li>')
        out.append(f'      <div class="nav-part">\n        <p class="nav-part-title">{part}</p>\n'
                   f'        <ol>\n' + '\n'.join(lis) + '\n        </ol>\n      </div>')
    return '\n'.join(out)


def shell(page, idx, body_html, masthead_html):
    prev_a = next_a = ''
    if idx > 0:
        p = PAGES[idx - 1]
        prev_a = (f'<a class="prev" href="{p["file"]}"><div class="dir">Previous</div>'
                  f'<div class="ttl">{p["title"]}</div></a>')
    if idx < len(PAGES) - 1:
        p = PAGES[idx + 1]
        next_a = (f'<a class="next" href="{p["file"]}"><div class="dir">Next</div>'
                  f'<div class="ttl">{p["title"]}</div></a>')

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page['title']} &middot; MOF Graphs and Crystal Morphology</title>
<meta name="description" content="{html.escape(page['desc'], quote=True)}">
<meta name="author" content="P. M. Radha Krishna, P. Kshitij Varma, G. Rohith Abhinav, J. Keerthi Sree, Isha">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='3' width='18' height='18' rx='3' fill='%2324459a'/%3E%3Cpath d='M8 16V8l4 5 4-5v8' fill='none' stroke='white' stroke-width='2' stroke-linejoin='round'/%3E%3C/svg%3E">
<link rel="preload" href="assets/fonts/source-serif-4-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
{THEME_INIT}
<link rel="stylesheet" href="assets/tokens.css">
<link rel="stylesheet" href="assets/base.css">
<link rel="stylesheet" href="assets/design.css">
<link rel="stylesheet" href="assets/study.css">
</head>
<body>

<a class="skip-link" href="#main">Skip to content</a>

<header class="site-header">
  <button class="nav-toggle" id="nav-toggle" type="button" aria-controls="sidebar" aria-expanded="false">
    <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5.5h14M3 10h14M3 14.5h9" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    <span>Contents</span>
  </button>
  <a class="brand" href="index.html">MOF Graphs and Crystal Morphology</a>
  <div class="header-tools">
    <button id="theme-btn" class="icon-btn" type="button" aria-label="Toggle colour theme"></button>
  </div>
</header>

<div class="layout">
  <aside class="sidebar" id="sidebar" aria-label="Contents">
    <nav class="site-nav" aria-label="All pages">
{sidebar(page)}
    </nav>
  </aside>
  <div class="sidebar-scrim" id="sidebar-scrim" hidden></div>

  <div class="page-col">
{masthead_html}
    <div class="container">
      <div class="with-toc">
        <main id="main">
{body_html}
          <nav class="page-nav" aria-label="Previous and next page">{prev_a}{next_a}</nav>
        </main>
        <aside id="toc" class="toc" aria-label="On this page"></aside>
      </div>
    </div>

    <footer class="site-footer">
      <div class="container">
        The network, spectrum and shape-explorer numbers are computed in your browser from the CIF
        files when the page loads; the other pages are generated from the result files of the Python
        code by <code>website/_build/</code>, and the test suites in <code>website/tests/</code> check every
        page against those files. Each figure names the script that produced it.
        23CSE498 Final Year Project, Amrita Vishwa Vidyapeetham, Coimbatore.
        <a href="https://github.com/Radha-Krishna-19/fyp">Source repository</a>
      </div>
    </footer>
  </div>
</div>

<script src="assets/palette.js"></script>
<script src="assets/glossary-data.js"></script>
<script src="assets/glossary.js"></script>
<script src="assets/site.js"></script>
{script_tags(SCRIPTS[page['file']])}
</body>
</html>
"""


def step_of(idx):
    """Where this page sits: its part, and its place in the reading sequence."""
    here = PAGES[idx]['file']
    part = next(name for name, items in PARTS if here in [f for f, _ in items])
    steps = [p for p in PAGES if p['file'] not in REFERENCE]
    names = [p['file'] for p in steps]
    if here not in names:
        return f'<div class="place ref">{part}. Reference material, outside the reading sequence.</div>'
    n = names.index(here) + 1
    return f'<div class="place">{part}. Chapter {n} of {len(steps)}.</div>'


def masthead(page, idx, extra=''):
    return f"""<div class="masthead">
  <div class="container">
{step_of(idx)}
    <h1>{page['title']}</h1>
    <p class="lead">{page['desc']}</p>
{extra}  </div>
</div>
"""


def add_figure_sources(html, page):
    """Add a Source line (script and data) under every figure image that has none."""
    from figure_sources import FIGURE_SOURCES, source_line
    def repl(m):
        fig = m.group(0)
        if 'class="provenance' in fig:
            return fig
        srcs = re.findall(r'<img[^>]*src="(figures/[^"]+)"', fig)
        if not srcs:
            return fig
        missing = [x for x in srcs if x not in FIGURE_SOURCES]
        if missing:
            sys.exit(f'{page}: no source recorded for {missing} in _build/figure_sources.py')
        lines = ''.join(source_line(x) for x in dict.fromkeys(srcs))
        return fig.replace('</figure>', lines + '</figure>')
    out, pos = [], 0
    for m in re.finditer(r'<figure\b.*?</figure>', html, flags=re.S):
        out.append(html[pos:m.start()])
        following = html[m.end():m.end() + 300]
        out.append(m.group(0) if 'class="provenance' in following.split('<figure')[0] else repl(m))
        pos = m.end()
    out.append(html[pos:])
    return ''.join(out)


def main():
    src = open(SRC, encoding='utf-8').read()
    sec = slice_sections(src)
    where = {}
    for p in PAGES:
        for s in p['sections']:
            where[s] = p['file']

    missing = [s for p in PAGES for s in p['sections'] if s not in sec]
    if missing:
        sys.exit(f'sections in the plan but not in the source: {missing}')
    orphan = [s for s in sec if s not in where]
    if orphan:
        sys.exit(f'sections in the source but not placed on any page: {orphan}')

    # Hand-authored additions live as plain HTML fragments in _fragments/ so
    # they can be edited as HTML rather than as escaped strings inside JSON.
    # <page>.<slot>.html is picked up automatically; slots are masthead,
    # before and after.
    extras = {}
    for p in PAGES:
        stem = p['file'].replace('.html', '')
        for slot in ('masthead', 'before', 'after'):
            frag = os.path.join(FRAG, f'{stem}.{slot}.html')
            if os.path.exists(frag):
                extras.setdefault(p['file'], {})[slot] = open(frag, encoding='utf-8').read()

    for i, p in enumerate(PAGES):
        parts = []
        if extras.get(p['file'], {}).get('before'):
            parts.append(extras[p['file']]['before'])
        for n, sid in enumerate(p['sections'], 1):
            parts.append(fix_links(renumber(sec[sid], n), p['file'], where))
        if extras.get(p['file'], {}).get('after'):
            parts.append(extras[p['file']]['after'])

        # Number the sections in the order they finally appear on the page.
        # Doing it here rather than per-slice means hand-written fragments and
        # sliced sections are numbered by one rule, so a fragment inserted
        # between two sections cannot desynchronise the sequence.
        assembled = '\n'.join(parts)
        counter = [0]
        def bump(m):
            counter[0] += 1
            return f'{m.group(1)}{counter[0]}{m.group(2)}'
        assembled = re.sub(r'(<span class="(?:stitle-num|n)">)\d+(</span>)', bump, assembled)

        assembled = add_figure_sources(assembled, p['file'])

        head_extra = extras.get(p['file'], {}).get('masthead', '')
        out = shell(p, i, assembled, masthead(p, i, head_extra))
        open(os.path.join(OUT, p['file']), 'w', encoding='utf-8').write(out)
        print(f'{p["file"]:20s} {len(out)//1024:4d} KB  {len(p["sections"])} sections')

    print(f'\n{len(PAGES)} pages, all {len(sec)} source sections placed.')


if __name__ == '__main__':
    main()
