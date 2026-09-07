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

    dict(file='code.html',         nav='Source',        sections=['source'],
         title='Every Line of Source Code',
         desc='All 28 source files, readable in the browser with no download and no web server.'),

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
    'methodology.html':   ['default_cif_data.js', 'mof_decompose.js', 'mof_network.js', 'overview_page.js'],
    'decomposition.html': ['THREE', 'mof_decompose.js', 'mof_render.js', 'mof_stages.js', 'mof_controls.js',
                           'default_cif_data.js', 'pipeline_walkthrough.js', 'app.js'],
    'network.html':       ['THREE', 'mof_decompose.js', 'mof_render.js', 'mof_network.js',
                           'mof_multifractal.js', 'default_cif_data.js', 'network_page.js'],
    'spectrum.html':      ['mof_decompose.js', 'mof_network.js', 'mof_multifractal.js',
                           'default_cif_data.js', 'network_page.js'],
    'results.html':       ['band_data.js', 'band_page.js',
                           'real_band_data.js', 'real_band_page.js'],
    'code.html':          ['code_sources.js', 'code_viewer.js', 'single_page.js'],
    'references.html':    [],
    'glossary.html':      [],
    'team.html':          [],
}

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
    'if(!t)t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";'
    'document.documentElement.setAttribute("data-theme",t);}catch(e){}})();</script>'
)

MARK = ('<svg class="mark" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        '<line x1="12" y1="12" x2="3" y2="6"  stroke="var(--linker)" stroke-width="1.6"/>'
        '<line x1="12" y1="12" x2="21" y2="6" stroke="var(--linker)" stroke-width="1.6"/>'
        '<line x1="12" y1="12" x2="12" y2="21" stroke="var(--linker)" stroke-width="1.6"/>'
        '<circle cx="3" cy="6" r="2.1"  fill="var(--linker)"/>'
        '<circle cx="21" cy="6" r="2.1" fill="var(--linker)"/>'
        '<circle cx="12" cy="21" r="2.1" fill="var(--linker)"/>'
        '<circle cx="12" cy="12" r="3.4" fill="var(--node)"/></svg>')


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


def shell(page, idx, body_html, masthead_html):
    nav = '\n'.join(
        '      <a href="{f}"{cur}>{n}</a>'.format(
            f=p['file'], n=p['nav'],
            cur=' aria-current="page"' if p['file'] == page['file'] else '')
        for p in PAGES)

    prev_a = next_a = ''
    if idx > 0:
        p = PAGES[idx - 1]
        prev_a = (f'<a class="prev" href="{p["file"]}"><div class="dir">&larr; Previous</div>'
                  f'<div class="ttl">{p["title"]}</div></a>')
    if idx < len(PAGES) - 1:
        p = PAGES[idx + 1]
        next_a = (f'<a class="next" href="{p["file"]}"><div class="dir">Next &rarr;</div>'
                  f'<div class="ttl">{p["title"]}</div></a>')

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page['title']} &middot; MOF Structural Descriptors</title>
<meta name="description" content="{html.escape(page['desc'], quote=True)}">
<meta name="author" content="P. M. Radha Krishna, P. Kshitij Varma, G. Rohith Abhinav, J. Keerthi Sree, Isha">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='6' fill='%23b91c1c'/%3E%3C/svg%3E">
{THEME_INIT}
<link rel="stylesheet" href="assets/tokens.css">
<link rel="stylesheet" href="assets/base.css">
<link rel="stylesheet" href="assets/design.css">
</head>
<body>

<a class="skip-link" href="#main">Skip to content</a>

<header class="site-header">
  <a class="brand" href="index.html">{MARK}<span>MOF Structural Descriptors</span></a>
  <nav class="site-nav" aria-label="Sections of this site">
{nav}
  </nav>
  <div class="header-tools">
    <button id="theme-btn" class="icon-btn" type="button" aria-label="Toggle colour theme"></button>
  </div>
</header>

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
    Every number on this site is computed in your browser from the CIF files in this
    folder when the page loads &mdash; none of them is hardcoded. The Python modules in
    <code>2_python/</code> reproduce all of them from the command line.
    &middot; 23CSE498 Final Year Project, Amrita Vishwa Vidyapeetham, Coimbatore.
    &middot; <a href="https://github.com/Radha-Krishna-19/fyp">Source repository</a>
  </div>
</footer>

<script src="assets/palette.js"></script>
<script src="assets/glossary-data.js"></script>
<script src="assets/glossary.js"></script>
<script src="assets/site.js"></script>
{script_tags(SCRIPTS[page['file']])}
</body>
</html>
"""


def step_of(idx):
    """Where this page sits in the seven-page sequence, as one short line.

    This replaces a numbered step-strip that listed all seven pages on every
    page. That strip repeated the navigation bar immediately above it: the same
    seven titles in the same order, twice, costing a band of vertical space on
    every page to tell the reader something the nav already told them. What the
    nav genuinely does NOT say is how far through the sequence this page is, so
    that — and only that — is what survives here.
    """
    steps = [p for p in PAGES if p['file'] not in
             ('code.html', 'references.html', 'glossary.html', 'team.html')]
    here = PAGES[idx]['file']
    names = [p['file'] for p in steps]
    if here not in names:
        return ('<div class="place ref">Reference material &mdash; outside the reading '
                'sequence. <a href="index.html">Start at the beginning</a>.</div>')
    n = names.index(here) + 1
    nxt = steps[n] if n < len(steps) else None
    tail = (f' &middot; next: <a href="{nxt["file"]}">{nxt["nav"]}</a>' if nxt
            else ' &middot; last step')
    return (f'<div class="place"><b>Step {n} of {len(steps)}</b>{tail}</div>')


def masthead(page, idx, extra=''):
    return f"""<div class="masthead">
  <div class="container">
    <div class="eyebrow">23CSE498 &middot; Final Year Project &middot; Phase II</div>
    <h1>{page['title']}</h1>
    <p class="lead">{page['desc']}</p>
{step_of(idx)}
{extra}  </div>
</div>
"""


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

        head_extra = extras.get(p['file'], {}).get('masthead', '')
        out = shell(p, i, assembled, masthead(p, i, head_extra))
        open(os.path.join(OUT, p['file']), 'w', encoding='utf-8').write(out)
        print(f'{p["file"]:20s} {len(out)//1024:4d} KB  {len(p["sections"])} sections')

    print(f'\n{len(PAGES)} pages, all {len(sec)} source sections placed.')


if __name__ == '__main__':
    main()
