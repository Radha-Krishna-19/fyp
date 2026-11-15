"""The reading guide at the top of every content page (inserted by build_site.py into the masthead).

Each guide has four parts, so that a reader with no background can follow the page and a specialist can
see at once what is established science and what is this project's own work:
  voice      : which specialist the page is written as (the discipline whose standards it must meet)
  plain      : the page's point in plain words, with an everyday picture
  background : what was already known before this project (with the source named in the page)
  ours       : what this project did on the page, and how far it can be trusted
Edit the text here, then run build_site.py.
"""

GUIDES = {
    "index.html": dict(
        voice="the whole team, for a reader who has never met the subject",
        plain="A MOF is a crystal full of tiny holes, built like a scaffold from metal joints and organic rods. "
              "Gases go in and out of those holes, so MOFs can store or clean gases. This project asked two "
              "questions: can a quick graph measurement pick out promising MOFs (Part I), and can we work out, "
              "from a MOF's crystal file alone, which crystal shapes it can grow into (Part II).",
        background="MOFs, crystal symmetry, the BFDH rule and the Wulff construction are established science.",
        ours="A program that takes a MOF's crystal file (CIF) and computes the faces its symmetry allows and the "
             "shapes it can take, written twice (Python and JavaScript) and scored against 134 laboratory records. "
             "Part I is a documented negative result."),
    "journey.html": dict(
        voice="a research supervisor writing the project's history",
        plain="The order in which things were done, what each step was built on, which mistakes were made and how "
              "each was found and fixed.",
        background="The papers the project started from (listed under References).",
        ours="Every method, notebook and result of the project, in time order, with the reason for each choice."),
    "methodology.html": dict(
        voice="a software architect and research methodologist",
        plain="A map of the whole project: what goes in, what each program does with it, what comes out, and how "
              "each result was checked.",
        background="The published algorithms the project uses are named where they appear.",
        ours="The workflow, datasets and evaluation design chosen for this project."),
    "decomposition.html": dict(
        voice="a computational chemist",
        plain="To study a MOF as a network, it is first split into its building blocks: the metal clusters (the "
              "joints) and the organic linkers (the rods). This page shows how that split is done.",
        background="The metal-oxo decomposition algorithm is published (see the page); we did not invent it.",
        ours="Our implementation of it, run beside a live 3D model, and checked on known MOFs."),
    "network.html": dict(
        voice="a graph theorist",
        plain="Once a MOF is split into blocks, the blocks become dots and the bonds between them become lines: a "
              "network. This page defines every network term the project uses.",
        background="Graph theory and the periodic (quotient) graph of a crystal are established mathematics.",
        ours="How we build the periodic graph of each MOF and the measurements taken on it."),
    "spectrum.html": dict(
        voice="an applied mathematician",
        plain="The multifractal spectrum describes how unevenly a network's connections are spread out. Part I "
              "hoped its width (Δα) would tell good MOFs from poor ones without simulation.",
        background="Multifractal analysis of networks by box covering is a published method (see the page).",
        ours="Our computation of it on 138 MOFs. It turned out to measure mostly the size of the calculation, so "
             "the conclusions built on it are withdrawn (Results)."),
    "results.html": dict(
        voice="a statistician reviewing a negative result",
        plain="What Part I found, and why its main claims were withdrawn: the measured width kept growing as the "
              "piece of crystal analysed grew, so it described the calculation more than the MOF.",
        background="Finite-size effects and confounding are standard statistical concerns.",
        ours="The full band, the tests that exposed the size confound, and the withdrawn claims kept with their "
             "reasons."),
    "bridge.html": dict(
        voice="a materials scientist",
        plain="A MOF powder is a heap of tiny crystals. Gas gets into each crystal through its surface, so the "
              "crystal's shape matters. This page explains why the project moved from networks to crystal shape.",
        background="That crystal shape affects uptake rates is reported in the literature cited on the page.",
        ours="The reason for Part II, and a test of whether Part I's measurement sees crystal shape."),
    "learn_shape.html": dict(
        voice="a crystallographer teaching from first principles",
        plain="Everything needed to follow the shape work, one picture per idea: what a unit cell is, how crystal "
              "faces are named, what symmetry does and how crystals grow.",
        background="All of this page is established crystallography; nothing on it is our result.",
        ours="Only the figures and the way the ideas are put together."),
    "learn_energy.html": dict(
        voice="a computational chemist and a statistician teaching from first principles",
        plain="Why some crystal faces are cheaper to make than others, where the energies come from (simple bond "
              "counts, machine-learned models, quantum chemistry), and the statistics used to score predictions.",
        background="Surface energy, DFT, machine-learned potentials and the statistics used are established.",
        ours="Only the figures and the selection of what is needed for this project."),
    "morph_math.html": dict(
        voice="a mathematician",
        plain="Every rule the shape program uses, written as a statement and proved, so that nobody has to take "
              "the program's word for it. Each statement is also checked by a calculation in your browser.",
        background="Most of the facts are classical crystallography; the page cites them.",
        ours="The 16 propositions in this form, their proofs, and the numerical checks. The proofs have not yet "
             "been checked by a second team member."),
    "cif_to_shape.html": dict(
        voice="a crystallographer",
        plain="Give the page a crystal file and it works out, step by step and in your browser, which faces the "
              "crystal may have and what shape those faces make. This is the project's main tool.",
        background="Symmetry analysis, systematic absences and the BFDH rule are established methods.",
        ours="The program that chains them together from a CIF to a 3D shape, with every step shown, written "
             "twice (Python and JavaScript) and checked to agree."),
    "morphology.html": dict(
        voice="a crystallographer answering the panel's question",
        plain="The panel asked whether several crystal shapes can be generated from one MOF's unit cell. This "
              "page shows that they can: symmetry fixes which faces exist, and changing how fast each face grows "
              "moves the crystal along a family of shapes.",
        background="Wulff and BFDH shapes are established; their use for MOFs is reported in the literature.",
        ours="The shape families of four MOFs computed from their own cells, and a comparison with experiment."),
    "deform.html": dict(
        voice="a crystallographer",
        plain="The second reading of the panel's question: what happens to the crystal shape if the unit cell "
              "itself is stretched or sheared? Long cells give rods, flat cells give plates.",
        background="The link between cell shape and crystal habit is classical.",
        ours="Exact rules (Propositions 14 to 16) and 52 computed cases. The stretched cells are hypothetical "
             "frameworks, not real ones."),
    "graph_faces.html": dict(
        voice="a graph theorist and crystallographer",
        plain="Counting how many links between building blocks a face cuts gives a rough measure of how costly "
              "that face is. Cheaper faces grow slower and end up larger.",
        background="Periodic bond-chain theory (Hartman and Perdok) is established.",
        ours="Its computation on each MOF's own periodic graph, and the shapes that follow."),
    "surface_energy.html": dict(
        voice="a computational chemist",
        plain="A surface energy is the cost of cutting a crystal open along a plane. Here it is estimated by "
              "counting the bonds each cut breaks, with a small correction for weaker attractions.",
        background="Surface energy and the Wulff construction are established; UFF is a published force field.",
        ours="The cleavage energy of every face of four MOFs and the shapes that follow. The energy is in effect "
             "a broken-bond count (93–98 % of the value); it ranks faces, it is not an absolute energy."),
    "hybrid.html": dict(
        voice="a materials scientist",
        plain="Two shape rules exist, one from geometry (BFDH) and one from energies (Wulff). This page blends "
              "them with one weight and shows what each mixture predicts.",
        background="BFDH and Wulff are established; blending them is our construction.",
        ours="The blended rule and its results for four MOFs. No best weight is claimed, because none was chosen "
             "on held-out data."),
    "experiment.html": dict(
        voice="an experimental materials chemist and a statistician",
        plain="What real crystals of these MOFs look like in published experiments, and how well each of our "
              "shape methods predicts them.",
        background="The laboratory records come from 35 published papers, cited row by row.",
        ours="The collection of 134 records, the scoring of every method against them, and the machine-learned "
             "(CHGNet) surface energies."),
    "morphology_map.html": dict(
        voice="a mathematician and crystallographer",
        plain="One map on which every shape a cubic crystal can take has its own region. Each model of the project "
              "is a point on it, and laboratory series can be checked against it.",
        background="The cube–octahedron–dodecahedron family of cubic shapes is classical.",
        ours="The exact boundaries of the map, every project model placed on it, and six laboratory series "
             "tested against it."),
    "ml_energies.html": dict(
        voice="a computational chemist, with a machine-learning specialist for the last section",
        plain="The team's notebook cuts each crystal, caps the broken bonds with water, and asks a machine-learned "
              "model (CHGNet) for the energy. Six faces came out with a negative surface energy, which is "
              "impossible for a stable crystal. This page explains why and fixes it.",
        background="CHGNet, MACE-MP-0, water capping and the thermodynamics of water at surfaces are published "
                   "(see Sources).",
        ours="The cause of the negative values (the water reference, a capping bug and two lost fixes), the "
             "correction, its effect on every MOF, and its effect on the GNN that learns from these energies."),
    "advisor.html": dict(
        voice="a materials scientist advising a synthesis chemist",
        plain="For ten MOFs: the shape the structure tends to give, how hard it would be to push it to another "
              "shape, and how open each shape's surface is to CO₂ and N₂.",
        background="The laboratory shapes come from published papers; the gas sizes are standard.",
        ours="The predictions, the steering numbers and the access indicators. No adsorption is calculated; "
             "these are geometric indicators only."),
    "relation.html": dict(
        voice="a statistician",
        plain="Does the network measurement of Part I say anything about the crystal shape of Part II? Four "
              "tests check this.",
        background="Correlation and confounding are standard statistics.",
        ours="The four tests and their result: what looks like a relation is driven by graph size."),
    "lessons.html": dict(
        voice="the team, reviewing its own mistakes",
        plain="Every mistake made in the project, what it was, why it happened and how it was fixed.",
        background="—",
        ours="All of it. Nothing on this page is deleted when a mistake is fixed."),
    "team.html": dict(
        voice="the team",
        plain="How far each part of the project has got, what is still open, and where every deliverable is.",
        background="—",
        ours="The current status, dated."),
}


def guide_html(page_file):
    g = GUIDES.get(page_file)
    if not g:
        return ""
    return (
        '<dl class="bridge reading-guide">'
        f'<dt>In plain words</dt><dd>{g["plain"]}</dd>'
        f'<dt>Known before us (background)</dt><dd>{g["background"]}</dd>'
        f'<dt>Our work here (foreground)</dt><dd>{g["ours"]}</dd>'
        f'<dt>Written as</dt><dd>{g["voice"]}</dd>'
        '</dl>\n')
