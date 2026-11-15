// Builds G070_Phase2_Review.pptx: the same content and order as presentation.tex (college beamer format),
// as an editable PowerPoint deck with speaker notes. Run from this folder:  node make_pptx.js
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const F = (n) => path.join(__dirname, "figures", n);
const SK = process.env.PPTX_SKILL || "";

const THEME = {
  name: "G070 Amrita", headFontFace: "Arial", bodyFontFace: "Arial",
  colors: { dk1: "1A1A1A", lt1: "FFFFFF", dk2: "A4123F", lt2: "F6EEF1", accent1: "A4123F", accent2: "1E7D3A",
            accent3: "8A8A8A", accent4: "2E5C8A", accent5: "D98E04", accent6: "5B3A8C", hlink: "2E5C8A", folHlink: "5B3A8C" },
};
const MAROON = "A4123F", TINT = "F6EEF1", GREEN = "1E7D3A", GREY = "8A8A8A", INK = "1A1A1A";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";               // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "MOF Graphs and Crystal Morphology - Phase II Review (G070)";
pres.author = "Team G070";

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  objects: [
    { rect: { x: 0, y: 0, w: 10, h: 0.78, fill: { color: MAROON } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.3, y: 0.04, w: 9.4, h: 0.44, fontSize: 20, bold: true, color: "FFFFFF", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: 0.3, y: 0.46, w: 9.4, h: 0.28, fontSize: 11, color: "FFFFFF", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "G070 · 23CSE498 Phase II", options: { x: 0.3, y: 5.33, w: 4, h: 0.25, fontSize: 8, color: GREY, margin: 0 } } },
  ],
  slideNumber: { x: 9.2, y: 5.33, w: 0.5, h: 0.25, fontSize: 8, color: GREY },
});
pres.defineSlideMaster({ title: "PLAIN", background: { color: "FFFFFF" }, objects: [] });

function slide(title, sub, notes) {
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText(title, { placeholder: "title" });
  if (sub) s.addText(sub, { placeholder: "sub" });
  if (notes) s.addNotes(notes);
  return s;
}
// bullet list: items are strings or [boldLead, rest]
function bullets(s, items, o) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    if (Array.isArray(it)) {
      runs.push({ text: it[0] + " ", options: { bold: true, bullet: true, breakLine: false } });
      runs.push({ text: it[1], options: { breakLine: !last } });
    } else runs.push({ text: it, options: { bullet: true, breakLine: !last } });
  });
  s.addText(runs, Object.assign({ fontSize: 12, color: INK, valign: "top", paraSpaceAfter: 4, isTextBox: true, margin: 0.04 }, o));
}
function box(s, title, items, o) {
  s.addShape(pres.shapes.RECTANGLE, { x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: TINT }, line: { color: MAROON, width: 0.75 } });
  s.addText(title, { x: o.x, y: o.y, w: o.w, h: 0.3, fontSize: 12, bold: true, color: "FFFFFF", fill: { color: MAROON }, margin: 0.06, isTextBox: true });
  bullets(s, items, { x: o.x + 0.05, y: o.y + 0.34, w: o.w - 0.1, h: o.h - 0.38, fontSize: o.fs || 15 });
}
function table(s, rows, o) {
  const head = rows[0].map((c) => ({ text: c, options: { bold: true, color: "FFFFFF", fill: { color: MAROON } } }));
  const body = rows.slice(1).map((r) => r.map((c) => (typeof c === "string" ? { text: c } : c)));
  s.addTable([head, ...body], Object.assign({ fontSize: 10, color: INK, border: { type: "solid", color: "C9C9C9", pt: 0.5 }, margin: 0.04, valign: "middle" }, o));
}
function img(s, name, x, y, w, h) { s.addImage({ path: F(name), x, y, w, h, altText: name }); }
function fit(name, maxw, maxh) { // keep aspect
  const dims = { "MIL125_01.jpeg": [1118, 1445], "MIL125_11.jpeg": [1118, 1445], "attach.png": [2053, 1249], "bfdh.png": [1299, 704],
    "capping.png": [2400, 570], "gamma_mu_ZnBDC.png": [900, 600], "map_regions.png": [1280, 1040], "methods_vs_exp.png": [1358, 1477],
    "morph_path.png": [1900, 562], "morphology_grid.png": [2130, 1220], "spec_map_UiO66.png": [1118, 728], "water_price.png": [1500, 390] };
  const [W, H] = dims[name] || [650, 650]; const k = Math.min(maxw / W, maxh / H); return [W * k, H * k];
}
function imgFit(s, name, x, y, maxw, maxh, center = true) {
  const [w, h] = fit(name, maxw, maxh);
  img(s, name, center ? x + (maxw - w) / 2 : x, y, w, h); return [w, h];
}

// ---------------------------------------------------------------- title
{
  const s = pres.addSlide({ masterName: "PLAIN" });
  s.addText("Type 1: Research Project", { x: 7.6, y: 0.12, w: 2.25, h: 0.3, fontSize: 10, bold: true, color: "FFFFFF", fill: { color: MAROON }, align: "center", isTextBox: true });
  s.addImage({ path: path.join(__dirname, "logo.png"), x: 3.95, y: 0.2, w: 2.1, h: 0.61, altText: "Amrita logo" });
  s.addText("MOF Graphs and Crystal Morphology: Crystal Shapes of Metal–Organic Frameworks from the Unit Cell",
    { x: 0.8, y: 0.9, w: 8.4, h: 0.75, fontSize: 20, bold: true, color: MAROON, align: "center", isTextBox: true });
  s.addText("23CSE498 – Project Phase II (External Review)   |   Team Number: G070", { x: 0.8, y: 1.62, w: 8.4, h: 0.3, fontSize: 12, bold: true, align: "center", color: INK, isTextBox: true });
  table(s, [["S.No", "Register Number", "Student Name"],
    ["1", "CB.SC.U4CSE23134", "Pasupuleti Meena Radha Krishna"], ["2", "CB.SC.U4CSE23122", "Kshitij Varma Pinnamaraju"],
    ["3", "CB.SC.U4CSE23031", "Keerthi Sree Jonnakuti"], ["4", "CB.SC.U4CSE23141", "Rohith Abhinav Sai Komal Gullolla"],
    ["5", "CB.SC.U4CSE23029", "Isha Sri Prakash"]], { x: 2.2, y: 2.0, w: 5.6, colW: [0.6, 1.9, 3.1], fontSize: 11 });
  s.addText([{ text: "Guide: ", options: {} }, { text: "Dr. T. Ramraj", options: { bold: true } }, { text: ", Assistant Professor (Sl. Gd.), Department of CSE" }],
    { x: 1, y: 4.45, w: 8, h: 0.3, fontSize: 12, align: "center", color: INK, isTextBox: true });
  s.addText("16 November 2026", { x: 1, y: 4.8, w: 8, h: 0.3, fontSize: 11, align: "center", color: GREY, isTextBox: true });
  s.addNotes("Introduce the team and the question the panel asked after Review 1: given the unit cell of an established MOF, generate its crystal morphologies mathematically and computationally.");
}
{
  const s = slide("Guide Review & Submission Approval", "Confirmation of Project Review and Approval from Guide");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.1, w: 8.8, h: 3.9, fill: { color: "FFFFFF" }, line: { color: INK, width: 1 } });
  s.addText([{ text: "[Insert Screenshot of Guide Approval Email Here]", options: { bold: true, breakLine: true } },
    { text: "Mandatory: a clear, readable screenshot of the email from the project guide approving this presentation.", options: { fontSize: 11 } }],
    { x: 0.8, y: 2.4, w: 8.4, h: 1.2, fontSize: 14, align: "center", color: INK, isTextBox: true });
}

// ---------------------------------------------------------------- 1 problem
{
  const s = slide("1. Problem Definition & Research Motivation", "Problem statement and identified research gap",
    "The question is the panel's. Shape matters because gas enters through faces. Use the worked example: same volume, the needle has the shortest path L = V/A and fills about seven times faster than the cube, because diffusion time scales with L squared. Then the gap: DFT is too slow for MOF slabs, and nobody had an automated CIF to shape route checked against laboratory crystals.");
  box(s, "Problem Statement", [
    ["Core problem:", "given the unit cell (CIF) of an established MOF, generate the crystal shapes it can take, mathematically and computationally, and say which one it prefers."],
    ["Why shape matters:", "gas enters through faces. At equal volume V the path is L = V/A and filling time ∝ L². For V = 1000 µm³: cube L = 1.67 µm, plate 20×20×2.5 L = 1.00 µm, needle 2.5×2.5×160 L = 0.62 µm → the needle fills ≈ 7× faster."],
  ], { x: 0.3, y: 0.95, w: 4.55, h: 4.25 });
  box(s, "Existing Limitations & Research Gap", [
    ["Inorganic crystals:", "DFT surface energies + Wulff construction. MOF slabs have 200–600 atoms: DFT is too slow for screening."],
    ["MOF shape studies:", "mostly experimental, one framework and one additive at a time; ML on MOFs targets adsorption, not shape."],
    ["Gap:", "no automated route CIF → allowed faces → surface energies → Wulff shape → every reachable shape and its distance, checked against laboratory crystals."],
  ], { x: 5.15, y: 0.95, w: 4.55, h: 4.25 });
}
{
  const s = slide("1. Problem Definition & Research Motivation (contd.)", "Research objectives and status",
    "Go through the table quickly. Six of seven objectives are done; the seventh, a conditions to shape model, is not feasible with laboratory data for only 12 MOFs, and we say so.");
  const ok = (t) => ({ text: "✓ " + t, options: { color: GREEN } });
  const no = (t) => ({ text: "✗ " + t, options: { color: MAROON } });
  table(s, [["Objective", "What was built and how it was checked", "Status"],
    ["O1 Faces from symmetry", "spglib space group → allowed {hkl} with exact absences → BFDH, any lattice; 16 propositions; Python and browser engines agree; 138 dataset CIFs", ok("validated (P1 files excepted)")],
    ["O2 Energies + Wulff", "bond-count / UFF cleavage γ (cubic); team pipeline: block-intact slabs, water caps, CHGNet γ, Wulff", ok("main face right, 4 of 5 MOFs")],
    ["O3 Validate γ", "MACE-MP-0 re-scoring; slab thickness; thermodynamic water reference; DFT inputs", ok("ρ 0.94–1.00; DFT not run")],
    ["O4 Laboratory benchmark", "134 records, 35 papers, 12 MOFs; additive-free vs additive", ok("28/32 records; 73–97 %")],
    ["O5 Fast surrogate", "GNN on the slab graph; leave-MOF-out CV vs baselines", ok("done; behind a linear baseline")],
    ["O6 Shape space", "exact morphology map; morphology spectrum (team notebook v4)", ok("new")],
    ["O7 Conditions → shape", "laboratory data for 12 MOFs only; held-out-MOF model 5/32", no("not feasible yet")],
  ], { x: 0.3, y: 0.95, w: 9.4, colW: [1.7, 5.6, 2.1], fontSize: 10 });
}

// ---------------------------------------------------------------- 2 workflow
{
  const s = slide("2. Proposed Methodology & Overall Workflow", "End-to-end methodology / system workflow architecture",
    "Two tracks. Track A on the left is symmetry and geometry: it runs on any CIF in seconds. Track B on top is the machine-learned pipeline, steps 1 to 8, then the GNN that replaces relaxation, then step 14, the morphology spectrum, which Isha added in version 4. Both tracks are scored against the 134 laboratory records.");
  const stp = (t, x, y, col = MAROON, w = 1.18) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.72, rectRadius: 0.06, fill: { color: col === MAROON ? TINT : "E9F3EC" }, line: { color: col, width: 1 } });
    s.addText(t, { x, y, w, h: 0.72, fontSize: 9, align: "center", valign: "middle", color: INK, margin: 0.02, isTextBox: true });
  };
  const arrow = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001, flipH: x2 < x1, flipV: y2 < y1, line: { color: "555555", width: 1.25, endArrowType: "triangle" } });
  const top = ["Any MOF CIF", "1 Standardize + space group", "2 Building-block graph", "3 Faces + absences", "4 Block-intact slabs", "5 Heal: H₂O → OH⁻ + H⁺", "6 CHGNet γ at Δμ(H₂O)"];
  top.forEach((t, i) => { stp(t, 0.3 + i * 1.34, 1.0); if (i) arrow(0.3 + i * 1.34 - 0.16, 1.36, 0.3 + i * 1.34, 1.36); });
  const row2 = [["9–12 Training data, CV, model", MAROON], ["13 GNN: CIF → γ in seconds", GREEN], ["14 Morphology spectrum", GREEN], ["8 Wulff shape", MAROON], ["7 MACE, thickness, DFT inputs", MAROON]];
  row2.forEach(([t, c], i) => stp(t, 3.0 + i * 1.34, 2.1, c));
  arrow(8.34 + 0.59, 1.72, 8.34 + 0.59, 2.1);                         // 6 -> 7
  arrow(8.34, 2.46, 8.18, 2.46); arrow(7.0, 2.46, 6.84, 2.46);       // 7 -> 8 -> 14
  arrow(4.18, 2.46, 4.34, 2.46); arrow(5.52, 2.46, 5.68, 2.46);       // 9-12 -> 13 -> 14
  stp("BFDH + morphology map", 0.3, 2.1); arrow(0.89, 1.72, 0.89, 2.1);
  stp("134 lab records (35 papers)", 0.3, 3.2); stp("Benchmark: main face, habit", 1.64, 3.2); stp("Steering + gas access", 2.98, 3.2);
  arrow(1.48, 3.56, 1.64, 3.56); arrow(2.82, 3.56, 2.98, 3.56); arrow(0.89, 2.82, 2.0, 3.2);
  s.addText([{ text: "Workflow summary. ", options: { bold: true } },
    { text: "Track A (left): symmetry → allowed faces → BFDH → map, seconds for any CIF. Track B (top): steps 1–8 give per-face γ and a Wulff shape; 9–13 train a GNN that replaces relaxation; 14 (green, new in notebook v4) lists every shape the faces can make and how far each is. Both tracks are scored against laboratory crystals." }],
    { x: 4.4, y: 3.15, w: 5.3, h: 1.95, fontSize: 11, color: INK, fill: { color: TINT }, margin: 0.1, isTextBox: true, valign: "top" });
}

// ---------------------------------------------------------------- 3 formulation
{
  const s = slide("3. Methodological Components & Formulation", "Governing mathematical model (1/2): faces and shapes",
    "Allowed faces come from the space group alone. Absence rule: an operation with hR = h and h·t not an integer kills that reflection; then d_eff = d/n. For ZIF-8, body-centred, {110} is allowed at first order with 12.0 Å, so it grows as a rhombic dodecahedron. Wulff: the shape depends only on energy ratios; the cubic map has exact boundaries. Attachment numbers explain the MOF-5 cube and the UiO-66 octahedron.");
  box(s, "Allowed faces from the space group", [
    "d_hkl = 1/‖h G⁻¹‖ ; cubic: d = a/√(h²+k²+l²)",
    "Absence: reflection n·h extinct if ∃(R,t) with hR = h and h·t ∉ ℤ; first allowed n gives d_eff = d_hkl/n",
    "I-centring: h+k+l even; F: h,k,l all even or all odd",
    "ZIF-8 (I-43m, a = 16.99 Å): d_eff {110} 12.0, {100} 8.5, {111} 4.9 Å → rhombic dodecahedron",
    "BFDH: face distance ∝ 1/d_eff; F-cubic {111}:{100} = 1 : 1.155 → truncated octahedron (78 % {111})",
  ], { x: 0.3, y: 0.95, w: 4.55, h: 4.25 });
  box(s, "Wulff construction and the cubic map", [
    "min Σ γᵢAᵢ at fixed V ⇒ W = {x : n̂ᵢ·x ≤ γᵢ ∀i} (half-space intersection; an LP detects open shapes)",
    "Shape depends only on ratios: x = γ110/γ100, y = γ111/γ100",
    "Cube: y ≥ √3 and x ≥ √2; octahedron: y ≤ 1/√3; cuboctahedron: y = 2/√3",
    "Attachment numbers: pcu {100},{110},{111} = 1,2,3 → cube; fcu {111},{100},{110} = 3,4,5 → octahedron",
    "Cell stretch c → λc: height/width = 1/λ for λ ≳ 0.8 (box law)",
  ], { x: 5.15, y: 0.95, w: 4.55, h: 4.25 });
}
{
  const s = slide("3. Methodological Components & Formulation (contd.)", "Governing mathematical model (2/2): surface energy, water, spectrum, GNN",
    "The surface energy subtracts the water used for caps. Water must be priced at a chemical potential with a stated condition; at 0 K it is the cheapest possible and gamma can go negative. The spectrum distance is the largest minus smallest log change of the energies: scale-free. The GNN uses message passing, softplus output, Huber loss plus a ranking loss.");
  box(s, "Surface energy with a water reservoir", [
    "γ = (E_slab − N·e_bulk − n·μ_H₂O) / 2A ;  1 eV/Å² = 16.02 J/m²",
    "γ(Δμ) = γ₀K − n·Δμ / 2A  (N formula units, n caps, A one face)",
    "Δμ (NIST-JANAF, CODATA): vapour 298 K −0.481; liquid 298 K −0.570; 50 % RH −0.587; 400 K −0.686 eV (ZPE omitted, ±0.1 eV)",
    "Bond-count: γ ≈ Σ_cut ε_b / 2A (UFF); 93–98 % of γ is broken bonds",
  ], { x: 0.3, y: 0.95, w: 4.55, h: 4.25 });
  box(s, "Morphology spectrum (v4) and GNN", [
    "Distance: s = maxₖ ln(gₖ/g₀ₖ) − minₖ ln(gₖ/g₀ₖ); Δ = (eˢ − 1)·100 % — scale-free, any reference face",
    "Scan: grid 0.3–2.5, step 0.05 (cubic, 2 025 shapes) or Sobol (4 faces); nearest point per class refined by bisection along ln g, then re-checked",
    "Class = habit name + faces with ≥ 5 % of the area",
    "GNN: message passing on the healed-slab atom graph → softplus → γ; loss = Huber(δ = 0.3) + 0.5 × pairwise rank loss; pretrained on static γ",
  ], { x: 5.15, y: 0.95, w: 4.55, h: 4.25 });
}
{
  const s = slide("3. Methodological Components & Formulation (contd.)", "Datasets, partitioning and evaluation metrics",
    "Datasets: 138 dataset CIFs, the RASPA2 library for slabs, and our 134 laboratory records with sources. Metrics: main face and habit against records with a paper-held-out baseline; leave-one-MOF-out for the GNN; Spearman between CHGNet and MACE; spectrum distance to the laboratory class.");
  box(s, "Dataset & input specifications", [
    ["Structures:", "138 dataset CIFs (77 hMOF, 61 CoRE MOF); RASPA2 library (105 readable; 16 MOFs relaxed, 41 static for pretraining)"],
    ["Laboratory morphology:", "134 records, 35 papers, 12 MOFs: additive, solvent, T, habit, faces, locator"],
    ["Preprocessing:", "disorder (majority), guests removed, overlaps merged; symmetry retried without H (ZIF-8 is P1 with H, I-43m without)"],
  ], { x: 0.3, y: 0.95, w: 4.55, h: 4.25 });
  box(s, "Partitioning & metrics", [
    ["Main face / habit accuracy", "vs records; baseline = lab majority with the paper held out; bootstrap over papers"],
    ["GNN:", "leave-one-MOF-out (16 folds): MAE, Spearman of face order, lowest face, main face"],
    ["CHGNet vs MACE:", "Spearman ρ and MAE of γ"],
    ["Spectrum:", "distance Δ to the laboratory class"],
  ], { x: 5.15, y: 0.95, w: 4.55, h: 4.25 });
}

// ---------------------------------------------------------------- 4 implementation
{
  const s = slide("4. Implementation Details – Overview", "Module-wise implementation and pipeline integration (steps 1–5)",
    "Steps 1 to 5: read and clean the CIF, find the building blocks, list face families with exact absences, cut slabs that keep every cluster and linker whole, and cap the cut bonds with OH and H.");
  table(s, [["Module", "Functionality"],
    ["1. Standardization", "CIF from RASPA2 URL, CoRE MOF refcode or upload; partial occupancy, guests, overlaps; spglib with fallback to the H-free or metal–carbon skeleton"],
    ["2. Building blocks", "bond graph: organic, metal–metal, metal–oxo, metal–ligand; components without M–L edges = nodes and linkers; periodic rods from lattice-image offsets"],
    ["3. Face families", "Miller indices to max_index, grouped by h' = hR⁻¹ (+ inversion), ranked by d_eff with exact absences; top N = 4"],
    ["4. Slab construction", "block centroids on n̂ → layers; one termination per gap; 15 Å slab, 15 Å vacuum; whole formula units asserted; broken bonds per area"],
    ["5. Surface healing", "exposed metal + OH (2.0 Å), donor O + H (0.98 Å) along the most open direction (Fibonacci sphere); clashes or broken organic bonds reject the slab"],
  ], { x: 0.3, y: 0.95, w: 9.4, colW: [2.0, 7.4], fontSize: 11 });
}
{
  const s = slide("4. Implementation Details – Overview (contd.)", "Module-wise implementation and pipeline integration (steps 6–14, website)",
    "Steps 6 to 14 and the environment. The final team notebook is Isha's version 4 file. The website is built from fragments and tested by 15 jsdom suites.");
  table(s, [["Module", "Functionality"],
    ["6. Surface energy", "CHGNet static screen of all terminations; best K = 2 relaxed to F_max < 0.05 eV/Å (800 steps); γ from slab, bulk, water; cached"],
    ["7. Validation", "MACE-MP-0 single points on CHGNet geometries; thicker-slab check; CP2K PBE-D3 inputs (normal along z, dipole correction)"],
    ["8. Wulff morphology", "lowest converged γ per family → half-space intersection → area fractions, habit, image, OBJ"],
    ["9–13. GNN surrogate", "RASPA2 survey → slab graphs → leave-MOF-out CV vs 5 baselines → final model → new CIF → γ → Wulff without CHGNet"],
    ["14. Morphology spectrum", "morphspec.py: favoured shape + every class with its distance; 14a self-tests, 14b one CIF, 14c all MOFs"],
    ["Track A + website", "mofmorph (Python) and browser engines; 28 pages from fragments; 15 jsdom suites"],
  ], { x: 0.3, y: 0.95, w: 9.4, colW: [2.0, 7.4], fontSize: 11 });
  s.addText([{ text: "Environment: ", options: { bold: true } }, { text: "Python (pymatgen, spglib, ASE, networkx, SciPy, PyTorch), CHGNet and MACE-MP-0 on a Colab GPU; JavaScript engines. Final notebook: MOF_Wulff_steps1-8_plus_GNN_v4.ipynb. Repository: github.com/Radha-Krishna-19/fyp" }],
    { x: 0.3, y: 4.45, w: 9.4, h: 0.75, fontSize: 11, color: INK, fill: { color: TINT }, margin: 0.08, isTextBox: true });
}
{
  const s = slide("5. Core Module Implementation Details", "Internal module mechanics, parameters and interfaces",
    "Two core modules. The slab builder and healer: cut only metal-ligand bonds; the capping rule must give at most one H to a donor oxygen, otherwise an impossible C-OH2+ appears, which happened in 26 of 118 slabs under the old rule. The spectrum module takes the lattice, faces and energies and returns the classes and distances.");
  box(s, "Slab builder & healer (block_slabs, heal)", [
    ["In/Out:", "conventional cell + (hkl) → terminations (slab, broken bonds, n caps)"],
    ["Rule:", "cut only metal–ligand bonds; a bridging O losing two bonds gets at most one H (else C–OH₂⁺: 26 of 118 slabs under the old rule)"],
    ["Parameters:", "15 Å slab, 15 Å vacuum, level_tol 0.3 Å, max_terms 8, M–X 2.55 Å, M–M 2.80 Å"],
  ], { x: 0.3, y: 0.95, w: 4.6, h: 2.25, fs: 14 });
  box(s, "Spectrum (scan_morphology_map)", [
    ["In:", "lattice, families, rotations, γ₀, BFDH point. Out: classes, distances, map, Wulff images"],
    ["Mechanics:", "class = habit + faces ≥ 5 %; 12-step bisection; cache on rounded ratios"],
  ], { x: 0.3, y: 3.3, w: 4.6, h: 1.9, fs: 14 });
  const calls = ["standardize() → conv, R, space group", "building_blocks() → nodes, linkers", "face_families() → {hkl}, d_eff", "block_slabs() + heal()", "Engine.relax() → γ(Δμ)", "wulff() → shape", "scan_morphology_map() → classes + Δ"];
  calls.forEach((t, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.6, y: 0.98 + i * 0.6, w: 3.6, h: 0.44, rectRadius: 0.05, fill: { color: "FFFFFF" }, line: { color: i === 6 ? GREEN : "555555", width: 1 } });
    s.addText(t, { x: 5.6, y: 0.98 + i * 0.6, w: 3.6, h: 0.44, fontSize: 10, fontFace: "Courier New", align: "center", valign: "middle", color: INK, isTextBox: true, margin: 0 });
    if (i) s.addShape(pres.shapes.LINE, { x: 7.4, y: 0.98 + i * 0.6 - 0.16, w: 0.001, h: 0.16, line: { color: "555555", width: 1.25, endArrowType: "triangle" } });
  });
}

// ---------------------------------------------------------------- 6 results
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration", "Structure-only models against 134 laboratory records",
    "Left: shapes of four MOFs from three models. Right: the score. Without additives the bond-count Wulff model gets the main face of 28 of 32 records, as good as using the laboratory majority, without seeing any laboratory data. With additives nothing structure-only works. BFDH gets the habit right for 85 of 97 records and predicts the Mg-MOF-74 rods.");
  imgFit(s, "morphology_grid.png", 0.3, 0.95, 5.0, 3.6);
  s.addText("Predicted habits of four MOFs from three surface models", { x: 0.3, y: 3.95, w: 5.0, h: 0.25, fontSize: 9, color: GREY, align: "center", isTextBox: true });
  table(s, [["Main face", "No additive (32)", "Additive (44)", "All (76)"],
    ["BFDH", "56 %", "48 %", "51 %"], [{ text: "Bond-count Wulff", options: { bold: true } }, { text: "88 %", options: { bold: true, color: GREEN } }, "39 %", "59 %"],
    ["Lab majority, paper out", "88 %", "30 %", "54 %"], ["Other MOFs, MOF out", "16 %", "39 %", "29 %"]],
    { x: 5.5, y: 0.95, w: 4.2, colW: [1.6, 0.95, 0.85, 0.8], fontSize: 10 });
  bullets(s, ["Additive-free: MOF-5 9/9, ZIF-8 11/12, HKUST-1 7/8, IRMOF-3 1/1, UiO-66 0/2 → 4 of 5 MOFs; paper bootstrap 73–97 %",
    "Habit: BFDH 85/97 vs 76 for 'always compact'; predicts Mg-MOF-74 rods (9/10 elongated)", "With additives no structure-only model is reliable"],
    { x: 5.5, y: 2.85, w: 4.2, h: 2.3, fontSize: 11 });
}
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration (contd.)", "The space of shapes: one exact map and one family",
    "The map: every cubic shape is a region of two energy ratios, with exact boundaries. The strip: cube to octahedron as the {111} to {100} distance ratio falls from infinity through 2 over root 3 to 1 over root 3. Attachment numbers: a new node lands with 1, 2 or 3 bonds on MOF-5 faces, so {100} grows slowest and the crystal is a cube; for UiO-66 the order is reversed. MOF-5 steering numbers.");
  imgFit(s, "map_regions.png", 0.3, 0.92, 4.0, 3.3);
  imgFit(s, "morph_path.png", 4.5, 0.92, 5.2, 1.5);
  imgFit(s, "attach.png", 4.5, 2.45, 5.2, 1.85);
  bullets(s, ["Strip: t = d111/d100 from ∞ (cube) via 2/√3 (cuboctahedron) to 1/√3 (octahedron)",
    "MOF-5: x = 2.81, y = 1.73 → cube; {111} must fall 38.1 % to dominate, 66.6 % for an octahedron"],
    { x: 0.3, y: 4.35, w: 9.4, h: 0.85, fontSize: 11 });
}
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration (contd.)", "Machine-learned energies: why six γ were negative, and the correction",
    "Each cut metal-oxygen bond is capped with water split into OH minus and H plus. The 14 November notebook priced that water at a free molecule at 0 K, the cheapest it can ever be, so capping looked like pure gain. Pricing water at liquid water fixes it. Worked case ZnBDC {001}: slope 0.308 per eV; minus 0.024 becomes plus 0.151.");
  imgFit(s, "capping.png", 0.3, 0.9, 9.4, 1.6);
  imgFit(s, "gamma_mu_ZnBDC.png", 0.3, 2.55, 4.3, 2.7);
  bullets(s, ["Water caps: OH⁻ on the metal, H⁺ on the O. The 14 Nov notebook priced each water at a free molecule at 0 K, the cheapest possible, so capping looked like pure gain",
    "ZnBDC {001}: n = 4, A = 104.08 Å² → n/2A = 0.308 J/m² per eV; γ = −0.024 + 0.308 × 0.5695 = +0.151 J/m² at liquid water",
    "Also fixed: one H per donor O; Mg–O rod kept whole; relaxed-cell slabs; hydroxylated UiO-66; exact face ranking; shape names; DFT input geometry"],
    { x: 4.8, y: 2.6, w: 4.9, h: 2.6, fontSize: 11 });
}
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration (contd.)", "Corrected GPU run (15 Nov): 98 relaxed slabs, 16 MOFs, liquid water",
    "After the corrections, the run on Kshitij's GPU: none of 98 slabs is negative at liquid water. ZIF-8, HKUST-1 main face and Mg-MOF-74 match the laboratory; UiO-66 still does not. Thickness and MACE checks.");
  ["wulff_ZIF8.png", "wulff_HKUST1.png", "wulff_MgMOF74.png", "wulff_UiO66.png"].forEach((n, i) => img(s, n, 0.55 + i * 2.3, 0.88, 1.75, 1.75));
  const ok = (t) => ({ text: t + " ✓", options: { color: GREEN } });
  table(s, [["MOF", "Before (14 Nov)", "Corrected, liquid water", "Laboratory"],
    ["ZIF-8", "rhombic dodecahedron", "{110} 100 %", ok("rhombic dodecahedron")],
    ["HKUST-1", "truncated octahedron", "{111} 66 %, {100} 33 %", ok("octahedron {111} (main face)")],
    ["Mg-MOF-74", "no shape (γ < 0)", "hexagonal rod, {2̄10} 77 %, {101} 23 %", ok("rods along c")],
    ["UiO-66", "truncated octahedron", "{111} 81 %, {100} 18 %", { text: "cube without additives ✗", options: { color: MAROON } }]],
    { x: 0.3, y: 2.7, w: 9.4, colW: [1.3, 2.1, 3.2, 2.8], fontSize: 10.5 });
  s.addText("85 of 98 converged; 6 negative at 0 K, none at liquid water; ZIF-8 {110} 24 vs 36 Å: 0.0565 vs 0.0527 J/m²; MACE-MP-0 vs CHGNet: Spearman 0.94–1.00, MAE 0.010–0.028 J/m²",
    { x: 0.3, y: 4.6, w: 9.4, h: 0.6, fontSize: 11, color: INK, fill: { color: TINT }, margin: 0.08, isTextBox: true });
}
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration (contd.)", "GNN surrogate: leave-one-MOF-out cross-validation (16 MOFs, corrected labels)",
    "Isha's GNN predicts relaxed gamma in seconds. In leave-one-MOF-out it has MAE 0.131 against 0.088 for a straight line on broken bonds per area and 0.084 for rescaled static CHGNet. The reason: broken bonds already carry almost all of gamma. 16 MOFs is small.");
  s.addChart(pres.charts.BAR, [{ name: "MAE", labels: ["Static CHGNet, rescaled", "Line on bonds/area", "GNN", "Mean", "Line on BFDH", "Static CHGNet"], values: [0.084, 0.088, 0.131, 0.146, 0.150, 0.542] }],
    { x: 0.3, y: 0.95, w: 5.2, h: 4.2, barDir: "bar", showTitle: true, title: "Leave-MOF-out MAE (J/m²), lower is better", titleFontSize: 12, titleFontFace: "+mn-lt",
      chartColors: [MAROON], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelFormatCode: "0.000", dataLabelFontFace: "+mn-lt",
      catAxisLabelFontSize: 10, valAxisLabelFontSize: 9, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelColor: "333333", valAxisLabelColor: "666666",
      valGridLine: { color: "E5E5E5", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, catAxisOrientation: "maxMin", valAxisMaxVal: 0.6, valAxisMinVal: 0 });
  table(s, [["Model", "Spearman", "Lowest face", "Main face"],
    ["Static, rescaled", "0.68", "0.69", "0.75"], ["Bonds/area line", "0.68", "0.63", "0.88"], ["GNN", "0.45", "0.50", "0.75"]],
    { x: 5.7, y: 0.95, w: 4.0, colW: [1.45, 0.85, 0.85, 0.85], fontSize: 10 });
  bullets(s, ["GNN (built by Isha): relaxed γ from the unrelaxed slab in seconds instead of minutes of CHGNet relaxation",
    "Behind two one-parameter baselines: broken bonds per area carry most of γ (93–98 % in the bond-count model)",
    "16 MOFs is small; the target is CHGNet, not experiment"], { x: 5.7, y: 2.45, w: 4.0, h: 2.75, fontSize: 11 });
}
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration (contd.)", "Morphology spectrum on the corrected energies: how far is the laboratory shape?",
    "Isha's spectrum, run on our corrected energies. The map for UiO-66: each colour is a shape class, the star is our computed energies. Distances to the laboratory shape: zero for ZIF-8 and Mg-MOF-74, 37 percent for the HKUST-1 octahedron, for UiO-66 the octahedron grown with acids is 19.7 percent away but the additive-free cube is 80 percent away, so the miss is real.");
  imgFit(s, "spec_map_UiO66.png", 0.3, 0.92, 5.2, 3.5);
  table(s, [["MOF", "Favoured", "Distance to lab shape"],
    ["ZIF-8", "rh. dodecahedron", "0 % (same class)"], ["Mg-MOF-74", "hexagonal rod", "0 % (same class)"],
    ["HKUST-1", "trunc. octahedron", "octahedron 37.2 %"], ["UiO-66", "trunc. octahedron", "octahedron (with acid) 19.7 %; cube (no additive) 80.4 %"]],
    { x: 5.7, y: 0.95, w: 4.0, colW: [1.0, 1.25, 1.75], fontSize: 10 });
  bullets(s, ["Star = computed energies; triangle = BFDH; 13 classes per cubic MOF, 27 for Mg-MOF-74",
    "'Octahedron' = ≥ 95 % {111}; a perfect octahedron needs γ111/γ100 = 1/√3 (43.7 % for UiO-66)",
    "An additive binding {111} moves UiO-66 the observed way; the additive-free cube stays unexplained"],
    { x: 0.3, y: 4.45, w: 9.4, h: 0.8, fontSize: 10.5 });
}
{
  const s = slide("6. Experimental Visualizations & Prototype Demonstration (contd.)", "Morphology spectrum of MIL-125 (team run of notebook v4, by Isha)",
    "Isha ran her spectrum on MIL-125, a tetragonal titanium MOF with four faces, so the scan is three-dimensional. Favoured shape a {101} block; a plate is only 3.5 percent away with CHGNet energies, a rod 10.7 percent with the GNN. Those CHGNet values still use the 0 K water reference.");
  imgFit(s, "MIL125_11.jpeg", 0.3, 0.88, 2.6, 3.65);
  ["MIL125_21.jpeg", "MIL125_02.jpeg", "MIL125_05.jpeg", "MIL125_16.jpeg", "MIL125_07.jpeg", "MIL125_08.jpeg"].forEach((n, i) =>
    img(s, n, 3.15 + (i % 3) * 2.2, 0.88 + Math.floor(i / 3) * 1.85, 1.8, 1.8));
  s.addText("Tetragonal, four faces → 3-axis Sobol scan, 31 classes. Favoured: CHGNet block {101} 90 %; GNN block {101} 58 %, {110} 41 % (same class as BFDH). Nearest: plate 3.5 % (CHGNet), rod 10.7 % (GNN). CHGNet values use v4's 0 K water reference.",
    { x: 0.3, y: 4.6, w: 9.4, h: 0.6, fontSize: 10.5, color: INK, fill: { color: TINT }, margin: 0.08, isTextBox: true });
}

// ---------------------------------------------------------------- 7 justification
{
  const s = slide("7. Technical Justification, Design Trade-offs & Insights", "Methodological rationale and design trade-offs",
    "Why symmetry first, why water as a chemical potential, why block-intact cuts, why spectrum distances matter. Trade-offs: CHGNet instead of DFT for speed, index limits, keeping the GNN while reporting where a simple line wins.");
  box(s, "1. Methodological justification", [
    ["Symmetry first:", "absences are exact and free; they remove faces before any energy and already fix ZIF-8"],
    ["Stated thermodynamics:", "capped surfaces are open systems; water must be a chemical potential with a condition, or γ can turn negative"],
    ["Block-intact cuts:", "MOFs grow by whole clusters and linkers"],
    ["Spectrum distances:", "for cubic crystals the class list follows from symmetry; the distance is the structure-specific number an additive must achieve"],
  ], { x: 0.3, y: 0.95, w: 4.55, h: 4.25, fs: 14 });
  box(s, "2. Design & parameter trade-offs", [
    ["CHGNet vs DFT:", "200–600-atom slabs, tens per MOF: DFT needs HPC days, CHGNet minutes; relaxation lowers γ by 60–100 %, so values are relative"],
    ["Search limits:", "max_index 1, top-K = 2 relaxations; high-index faces cannot appear"],
    ["GNN vs baselines:", "kept because it is fast; reported honestly where a one-line model wins"],
  ], { x: 5.15, y: 0.95, w: 4.55, h: 4.25, fs: 14 });
}
{
  const s = slide("7. Technical Justification, Design Trade-offs & Insights (contd.)", "Boundary conditions, limitations and future scope",
    "Edge cases are rejected rather than hidden. The code-version point: the final team notebook keeps the 0 K reference, our reported energies come from the corrected run, and Isha's spectrum passes all its checks with either set of modules. Limitations: no DFT, UiO-66 cubes not reproduced. Next: DFT on one slab per MOF, modulator caps read through spectrum distances.");
  box(s, "3. Boundary conditions & edge cases", [
    ["P1 files:", "71 of 77 hMOF CIFs carry no symmetry: triclinic cell only"],
    ["Invalid slabs", "(not whole units, broken organic bonds, clashing caps) are rejected; open shapes named 'open'; γ ≤ 0 gives no shape"],
    ["Code versions:", "the final notebook (v4) keeps the 0 K water reference; energies reported here come from the corrected run; the spectrum passes 20/20 checks with either module set"],
  ], { x: 0.3, y: 0.95, w: 4.55, h: 4.25, fs: 14 });
  box(s, "4. Limitations & future scope", [
    ["Not validated:", "no γ checked by DFT (CP2K inputs ready); UiO-66 additive-free cubes not reproduced; records and proofs need a second check"],
    ["Equilibrium vs growth:", "lab crystals are shaped by growth rates and additives; Wulff is a baseline"],
    ["Next:", "DFT on one slab per MOF; modulator caps (formate, benzoate) at their own chemical potential, read through spectrum distances. Part I (Δα) closed as a negative result"],
  ], { x: 5.15, y: 0.95, w: 4.55, h: 4.25, fs: 14 });
}

// ---------------------------------------------------------------- references, thanks
{
  const s = slide("References", "");
  const refs = [
    "G. Wulff, Z. Kristallogr. 34, 449 (1901).", "J. D. H. Donnay and D. Harker, Am. Mineral. 22, 446 (1937).",
    "R. F. P. Grimbergen et al., Acta Cryst. A54, 491 (1998).", "B. Deng et al., CHGNet, Nat. Mach. Intell. 5, 1031 (2023).",
    "I. Batatia et al., MACE-MP-0, arXiv:2401.00096 (2024).", "Y. G. Chung et al., CoRE MOF 2019, J. Chem. Eng. Data 64, 5985 (2019).",
    "S. P. Ong et al., pymatgen, Comput. Mater. Sci. 68, 314 (2013).", "A. Togo et al., spglib, Sci. Technol. Adv. Mater. Methods 4, 2384822 (2024).",
    "A. K. Rappé et al., UFF, J. Am. Chem. Soc. 114, 10024 (1992).", "P. Chen et al., morphology of nanoscale MOFs, Matter 2, 1651 (2020).",
    "A. Umemura et al., coordination modulation, J. Am. Chem. Soc. 133, 15506 (2011).", "K. Reuter and M. Scheffler, Phys. Rev. B 65, 035406 (2001).",
    "M. W. Chase, NIST-JANAF Thermochemical Tables, 4th ed. (1998).", "J. Gilmer et al., neural message passing, ICML, PMLR 70, 1263 (2017).",
    "I. M. Sobol', USSR Comput. Math. Math. Phys. 7, 86 (1967).", "R. Tran et al., surface energies of elemental crystals, Sci. Data 3, 160080 (2016)."];
  s.addText(refs.map((r, i) => ({ text: `[${i + 1}] ${r}`, options: { breakLine: i < refs.length - 1 } })),
    { x: 0.4, y: 0.95, w: 9.2, h: 4.25, fontSize: 10.5, color: INK, valign: "top", paraSpaceAfter: 2, isTextBox: true });
}
{
  const s = pres.addSlide({ masterName: "PLAIN" });
  s.addText("Thank You", { x: 1, y: 1.8, w: 8, h: 1, fontSize: 44, bold: true, color: MAROON, align: "center", isTextBox: true });
  s.addText("Questions & Viva Voce", { x: 1, y: 2.85, w: 8, h: 0.5, fontSize: 20, bold: true, color: INK, align: "center", isTextBox: true });
}

(async () => {
  const out = path.join(__dirname, "G070_Phase2_Review.pptx");
  await pres.writeFile({ fileName: out });
  if (SK) { const { applyTheme } = require(path.join(SK, "scripts", "apply_theme.js")); await applyTheme(out, THEME); }
  console.log("wrote", out);
})();
