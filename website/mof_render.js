// mof_render.js
// Three.js scene builder for the pipeline-stage 3D viewer. Knows nothing about
// "stages" or the decomposition algorithm -- it just takes one DATA object
// (the shape produced by mof_decompose.js) plus a small "view options" object
// and draws it: atoms, bonds, optional coarse-grained block markers, unit
// cell, camera orbit controls, and a hover tooltip. mof_stages.js decides
// WHICH DATA + which view options belong to each pipeline stage; this file
// only renders whatever it's given.
//
// Exposed as window.MOFRender with methods:
//   init(canvas, container, labelsLayer, hoverTipEl)
//   load(DATA, viewOpts)   -- full (re)build of the scene from DATA
//   resize()
//
// viewOpts:
//   colorMode   : 'element' | 'metalNonmetal' | 'block'
//   showBonds   : bool
//   showCell    : bool
//   netOnly     : bool   -- true = hide real atoms/bonds, show only collapsed
//                           block centroid markers + inter-block edges
//                           (the Module 5/6 "simplified net" view)
//   dimNonHighlight : bool -- if true and colorMode='metalNonmetal' or 'block',
//                           nothing extra; reserved for future use

(function (root) {
  'use strict';

  const CPK = {
    H:0xdedede, He:0xd9ffff, Li:0xcc80ff, Be:0xc2ff00, B:0xffb5b5, C:0x909090, N:0x3050f8, O:0xe6362b, F:0x90e050,
    Na:0xab5cf2, Mg:0x8aff00, Al:0x848484, Si:0xf0c8a0, P:0xff8000, S:0xffff30, Cl:0x1ff01f,
    K:0x8f40d4, Ca:0x3dff00, Sc:0xe6e6e6, Ti:0xbfc2c7, V:0xa6a6ab, Cr:0x8a99c7, Mn:0x9c7ac7,
    Fe:0xe06633, Co:0xf090a0, Ni:0x50d050, Cu:0xc87a33, Zn:0x7d80b0, Ga:0xc28f8f, Ge:0x668f8f,
    As:0xbd80e3, Se:0xffa100, Br:0xa62929, Zr:0x94e0e0, Nb:0x73c2c9, Mo:0x54b5b5, Ru:0x248f8f,
    Rh:0x0a7d8c, Pd:0x006985, Ag:0xc0c0c0, Cd:0xffd98f, In:0xa67573, Sn:0x668080, Sb:0x9e63b5,
    Te:0xd47fb9, I:0x940094, La:0x70d4ff, Ce:0xffffc7, Hf:0x4dc2ff, Ta:0x4da6ff, W:0x2194d6,
    Re:0x267dab, Os:0x266696, Ir:0x175487, Pt:0xd0d0e0, Au:0xffd123, Hg:0xb8b8d0, Tl:0xa6544d,
    Pb:0x575961, Bi:0x9e4fb5,
  };
  const METAL_COLOR = 0xc0392b;      // binary "metal" color for the Module 3 view
  const NONMETAL_COLOR = 0x2e86c1;   // binary "nonmetal" color for the Module 3 view
  const NODE_COLOR = 0xc0392b;       // "node" block color for 4a/4b/4c views
  const LINKER_COLOR = 0x2e86c1;     // "linker" block color for 4a/4b/4c views
  const BLOCK_PALETTE = [
    0x8e44ad, 0xd97b1e, 0x2e86c1, 0x27ae60, 0xc0392b, 0x16a085,
    0xe67e22, 0x2980b9, 0xaf4bce, 0xf39c12, 0x1abc9c, 0xd35400,
    0x7f8c8d, 0x9b59b6,
  ];

  function elementColor(el) {
    if (CPK[el] !== undefined) return CPK[el];
    let h = 0; for (let i = 0; i < el.length; i++) h = (h * 31 + el.charCodeAt(i)) >>> 0;
    const c = new THREE.Color(); c.setHSL((h % 360) / 360, 0.5, 0.55);
    return c.getHex();
  }
  const COVR = (typeof MOFDecompose !== 'undefined' && MOFDecompose.COVALENT_RADII) || {};
  const METALS = (typeof MOFDecompose !== 'undefined' && MOFDecompose.METALS) || new Set();
  function elementRadius(el) {
    if (el === 'H') return 0.24;
    const cov = COVR[el];
    return cov ? Math.max(0.26, cov * 0.42) : 0.32;
  }

  // Element properties shown when an atom is clicked: name, atomic number, standard atomic weight
  // (IUPAC, rounded), Pauling electronegativity (null where no single accepted value), and the
  // kind of element. Group and period place it in the periodic table.
  const ELEMENTS = {
    H: ['Hydrogen', 1, 1.008, 2.20, 'nonmetal', 1, 1], He: ['Helium', 2, 4.0026, null, 'noble gas', 18, 1],
    Li: ['Lithium', 3, 6.94, 0.98, 'alkali metal', 1, 2], Be: ['Beryllium', 4, 9.0122, 1.57, 'alkaline-earth metal', 2, 2],
    B: ['Boron', 5, 10.81, 2.04, 'metalloid', 13, 2], C: ['Carbon', 6, 12.011, 2.55, 'nonmetal', 14, 2],
    N: ['Nitrogen', 7, 14.007, 3.04, 'nonmetal', 15, 2], O: ['Oxygen', 8, 15.999, 3.44, 'nonmetal', 16, 2],
    F: ['Fluorine', 9, 18.998, 3.98, 'halogen', 17, 2], Na: ['Sodium', 11, 22.990, 0.93, 'alkali metal', 1, 3],
    Mg: ['Magnesium', 12, 24.305, 1.31, 'alkaline-earth metal', 2, 3], Al: ['Aluminium', 13, 26.982, 1.61, 'post-transition metal', 13, 3],
    Si: ['Silicon', 14, 28.085, 1.90, 'metalloid', 14, 3], P: ['Phosphorus', 15, 30.974, 2.19, 'nonmetal', 15, 3],
    S: ['Sulfur', 16, 32.06, 2.58, 'nonmetal', 16, 3], Cl: ['Chlorine', 17, 35.45, 3.16, 'halogen', 17, 3],
    K: ['Potassium', 19, 39.098, 0.82, 'alkali metal', 1, 4], Ca: ['Calcium', 20, 40.078, 1.00, 'alkaline-earth metal', 2, 4],
    Sc: ['Scandium', 21, 44.956, 1.36, 'transition metal', 3, 4], Ti: ['Titanium', 22, 47.867, 1.54, 'transition metal', 4, 4],
    V: ['Vanadium', 23, 50.942, 1.63, 'transition metal', 5, 4], Cr: ['Chromium', 24, 51.996, 1.66, 'transition metal', 6, 4],
    Mn: ['Manganese', 25, 54.938, 1.55, 'transition metal', 7, 4], Fe: ['Iron', 26, 55.845, 1.83, 'transition metal', 8, 4],
    Co: ['Cobalt', 27, 58.933, 1.88, 'transition metal', 9, 4], Ni: ['Nickel', 28, 58.693, 1.91, 'transition metal', 10, 4],
    Cu: ['Copper', 29, 63.546, 1.90, 'transition metal', 11, 4], Zn: ['Zinc', 30, 65.38, 1.65, 'transition metal', 12, 4],
    Ga: ['Gallium', 31, 69.723, 1.81, 'post-transition metal', 13, 4], Ge: ['Germanium', 32, 72.630, 2.01, 'metalloid', 14, 4],
    Br: ['Bromine', 35, 79.904, 2.96, 'halogen', 17, 4], Sr: ['Strontium', 38, 87.62, 0.95, 'alkaline-earth metal', 2, 5],
    Y: ['Yttrium', 39, 88.906, 1.22, 'transition metal', 3, 5], Zr: ['Zirconium', 40, 91.224, 1.33, 'transition metal', 4, 5],
    Nb: ['Niobium', 41, 92.906, 1.6, 'transition metal', 5, 5], Mo: ['Molybdenum', 42, 95.95, 2.16, 'transition metal', 6, 5],
    Ru: ['Ruthenium', 44, 101.07, 2.2, 'transition metal', 8, 5], Rh: ['Rhodium', 45, 102.91, 2.28, 'transition metal', 9, 5],
    Pd: ['Palladium', 46, 106.42, 2.20, 'transition metal', 10, 5], Ag: ['Silver', 47, 107.87, 1.93, 'transition metal', 11, 5],
    Cd: ['Cadmium', 48, 112.41, 1.69, 'transition metal', 12, 5], In: ['Indium', 49, 114.82, 1.78, 'post-transition metal', 13, 5],
    Sn: ['Tin', 50, 118.71, 1.96, 'post-transition metal', 14, 5], I: ['Iodine', 53, 126.90, 2.66, 'halogen', 17, 5],
    Ba: ['Barium', 56, 137.33, 0.89, 'alkaline-earth metal', 2, 6], La: ['Lanthanum', 57, 138.91, 1.10, 'lanthanide', 3, 6],
    Ce: ['Cerium', 58, 140.12, 1.12, 'lanthanide', null, 6], Nd: ['Neodymium', 60, 144.24, 1.14, 'lanthanide', null, 6],
    Eu: ['Europium', 63, 151.96, null, 'lanthanide', null, 6], Gd: ['Gadolinium', 64, 157.25, 1.20, 'lanthanide', null, 6],
    Tb: ['Terbium', 65, 158.93, null, 'lanthanide', null, 6], Dy: ['Dysprosium', 66, 162.50, 1.22, 'lanthanide', null, 6],
    Er: ['Erbium', 68, 167.26, 1.24, 'lanthanide', null, 6], Yb: ['Ytterbium', 70, 173.05, null, 'lanthanide', null, 6],
    Hf: ['Hafnium', 72, 178.49, 1.3, 'transition metal', 4, 6], W: ['Tungsten', 74, 183.84, 2.36, 'transition metal', 6, 6],
    Pt: ['Platinum', 78, 195.08, 2.28, 'transition metal', 10, 6], Au: ['Gold', 79, 196.97, 2.54, 'transition metal', 11, 6],
    Hg: ['Mercury', 80, 200.59, 2.00, 'transition metal', 12, 6], Pb: ['Lead', 82, 207.2, 2.33, 'post-transition metal', 14, 6],
    Bi: ['Bismuth', 83, 208.98, 2.02, 'post-transition metal', 15, 6], U: ['Uranium', 92, 238.03, 1.38, 'actinide', null, 7],
  };
  function hexMix(a, b, t) {               // blend two 0xRRGGBB colours, t = share of b
    const ch = (x, k) => (x >> k) & 255;
    const m = k => Math.round(ch(a, k) * (1 - t) + ch(b, k) * t) << k;
    return m(16) | m(8) | m(0);
  }
  function hexCss(h) { return '#' + ('000000' + h.toString(16)).slice(-6); }
  // bond drawing: 'cloud' (default) = a smooth tube in the colours of its two atoms, slightly waisted
  // like a stretched elastic band, inside a soft translucent sheath suggesting the shared electron
  // density; 'stick' = the earlier thin grey sticks
  let BOND_STYLE = 'cloud';
  try { const v = localStorage.getItem('mofBondStyle'); if (v === 'cloud' || v === 'stick') BOND_STYLE = v; } catch (e) { /* storage blocked */ }
  const _allRenderers = [];

  // =================================================================
  // SHARED FRAME TICKER  (fixes the "3D stops working after a few
  // minutes" bug)
  //
  // The old code gave EVERY renderer instance its own uncapped
  // requestAnimationFrame loop, each re-rendering a completely STATIC
  // scene at 60fps forever. index.html builds 5 of them (1 walkthrough
  // + 4 drawback demos) and the embedded pipeline iframe added a 6th.
  // Six permanently-spinning WebGL contexts is enough for a browser to
  // start dropping the oldest context under memory/GPU pressure -- and
  // a dropped context just goes silently blank, which is exactly the
  // reported symptom.
  //
  // Fix, in three parts:
  //   1. ONE shared ticker for all instances (below), instead of N.
  //   2. On-demand rendering: an instance only issues GL calls when
  //      something actually changed (camera moved, new data loaded,
  //      resized) via requestRender(). A static scene now costs ~0.
  //   3. Instances that are scrolled off-screen don't render at all
  //      (IntersectionObserver), and any context the browser DOES
  //      drop is detected and automatically rebuilt (see initContextGuards).
  // =================================================================
  const _instances = [];
  let _tickerStarted = false;
  function _startTicker() {
    if (_tickerStarted || typeof requestAnimationFrame === 'undefined') return;
    _tickerStarted = true;
    (function loop() {
      requestAnimationFrame(loop);
      for (let i = 0; i < _instances.length; i++) {
        try { _instances[i]._frame(); } catch (e) { /* never let one panel kill the others */ }
      }
    })();
  }

  function makeRenderer() {
    let canvas, container, labelsLayer, hoverTip;
    let scene, renderer, camera;
    let rotGroup, atomGroup, bondGroup, blockGroup, cellGroup;
    let sphereGeo, cylGeo, blockGeoSphere, blockGeoBox, sharedGeos, bandGeo;
    let selected = null, infoCard = null, styleBar = null;
    let atomMeshes = [], bondMeshes = [], blockMeshes = [];
    let centerAll = null;
    let camYaw = 0.7, camPitch = 0.45, camDist = 30;
    let dragging = false, lastX = 0, lastY = 0, dragMoved = 0, touchLast = null;
    let currentData = null, currentOpts = {};
    // --- on-demand render state (see SHARED FRAME TICKER note above) ---
    let needsRender = true;     // dirty flag: true = something changed, re-render once
    let isVisible = true;       // false when scrolled off-screen -> skip rendering entirely
    let contextLost = false;    // true between webglcontextlost and webglcontextrestored
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    function requestRender() { needsRender = true; }

    // Called once per animation frame by the single shared ticker. Does
    // nothing at all unless this instance is visible AND actually dirty.
    function _frame() {
      if (!renderer || contextLost || !isVisible || !needsRender) return;
      needsRender = false;
      renderer.render(scene, camera);
      updateLabels();
    }

    function sizeRenderer() {
      const w = container.clientWidth, h = container.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      requestRender();
    }

    function updateCamera() {
      const x = centerAll.x + camDist * Math.cos(camPitch) * Math.sin(camYaw);
      const y = centerAll.y + camDist * Math.sin(camPitch);
      const z = centerAll.z + camDist * Math.cos(camPitch) * Math.cos(camYaw);
      camera.position.set(x, y, z);
      camera.lookAt(centerAll);
      requestRender();
    }

    function makeStub(startPos, dirVec, color) {
      const len = dirVec.length();
      if (len < 0.01) return null;
      const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.7 });
      const mesh = new THREE.Mesh(cylGeo, mat);
      mesh.scale.set(1, len, 1);
      const mid = startPos.clone().add(dirVec.clone().multiplyScalar(0.5));
      mesh.position.copy(mid);
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dirVec.clone().normalize());
      return mesh;
    }

    // A cloud bond from atom A towards the bond midpoint: the waisted tube in A's colour.
    function makeBand(startPos, dirVec, color, opacity) {
      const len = dirVec.length();
      if (len < 0.01) return null;
      const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.32, metalness: 0.05, transparent: opacity < 1, opacity });
      const mesh = new THREE.Mesh(bandGeo, mat);
      mesh.scale.set(1, len, 1);
      mesh.position.copy(startPos.clone().add(dirVec.clone().multiplyScalar(0.5)));
      // the cylinder's wide end (bottom, -y) sits at the atom: point +y along the bond
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dirVec.clone().normalize());
      return mesh;
    }
    // The translucent sheath around a whole bond: an elongated soft ellipsoid, added on top of what is
    // behind it (additive blending), so it reads as a glow of shared electrons rather than a solid.
    function makeSheath(pa, vec, color) {
      const len = vec.length();
      if (len < 0.01) return null;
      const opt = { color, roughness: 1, metalness: 0, transparent: true, opacity: 0.22, depthWrite: false };
      if (THREE.AdditiveBlending !== undefined) opt.blending = THREE.AdditiveBlending;
      const mat = new THREE.MeshStandardMaterial(opt);
      const mesh = new THREE.Mesh(sphereGeo, mat);
      mesh.scale.set(0.3, len * 0.56, 0.3);
      mesh.position.copy(pa.clone().add(vec.clone().multiplyScalar(0.5)));
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vec.clone().normalize());
      mesh.renderOrder = 2;
      return mesh;
    }

    function makeLabelEl(text, cls) {
      const el = document.createElement('div');
      el.className = cls;
      el.textContent = text;
      el.style.position = 'absolute';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.pointerEvents = 'none';
      el.style.whiteSpace = 'nowrap';
      el.style.textShadow = '0 0 3px #fff, 0 0 3px #fff, 0 0 5px #fff, 0 1px 1px rgba(0,0,0,0.4)';
      el.style.userSelect = 'none';
      el.style.color = PAL.text;
      labelsLayer.appendChild(el);
      return el;
    }
    const _projVec = new THREE.Vector3();
    function worldToScreen(pos, w, h) {
      _projVec.copy(pos).project(camera);
      return { x: (_projVec.x * 0.5 + 0.5) * w, y: (-_projVec.y * 0.5 + 0.5) * h, behind: _projVec.z > 1 };
    }
    function disposeGroup(group) {
      while (group.children.length) {
        const obj = group.children.pop();
        if (obj.geometry && !sharedGeos.has(obj.geometry)) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      }
    }

    /* -----------------------------------------------------------------
       BLOCK INSPECTOR

       Draws what is inside one coarse-grained vertex: the block's atoms and
       the bonds among them, projected onto the plane that shows the block
       most face-on, plus the stubs of the bonds that leave it.

       Why project rather than show a second 3D scene: a second WebGL context
       inside a tooltip is expensive, and browsers cap contexts per tab — the
       same reason the standalone pipeline viewer was removed from this site.
       A 2D projection costs nothing and answers the question being asked,
       which is "what is in there and how is it wired", not "what does it look
       like from every angle".

       The projection plane is chosen by principal axes: project onto the two
       directions in which the block is most spread out, so a flat linker is
       seen face-on rather than edge-on, where it would collapse to a line.
       ----------------------------------------------------------------- */
    function blockLocalGeometry(block) {
      if (!currentData || !block || !block.atoms) return null;
      const idx = block.atoms;
      const inBlock = new Set(idx);
      const pts = idx.map(i => currentData.atoms[i]).filter(Boolean);
      if (pts.length === 0) return null;

      // internal bonds, and the stubs of bonds that leave the block
      const internal = [], leaving = [];
      (currentData.bonds || []).forEach(bd => {
        const ina = inBlock.has(bd.a), inb = inBlock.has(bd.b);
        if (ina && inb) internal.push([bd.a, bd.b]);
        else if (ina || inb) leaving.push(ina ? bd.a : bd.b);
      });
      return { idx, pts, internal, leaving };
    }

    function principalPlane(pts) {
      // Centre, then take the two directions of greatest spread. Full PCA is
      // unnecessary here: a power iteration on the 3x3 covariance is exact
      // enough for choosing a viewing plane and is a few lines.
      const n = pts.length;
      const c = [0, 0, 0];
      pts.forEach(p => { c[0] += p.pos[0]; c[1] += p.pos[1]; c[2] += p.pos[2]; });
      c[0] /= n; c[1] /= n; c[2] /= n;
      const C = [[0,0,0],[0,0,0],[0,0,0]];
      pts.forEach(p => {
        const d = [p.pos[0]-c[0], p.pos[1]-c[1], p.pos[2]-c[2]];
        for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i][j] += d[i]*d[j];
      });
      function mul(M, v) {
        return [M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
                M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
                M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2]];
      }
      function norm(v) {
        const L = Math.hypot(v[0], v[1], v[2]) || 1;
        return [v[0]/L, v[1]/L, v[2]/L];
      }
      let u = norm([1, 0.3, 0.1]);
      for (let k = 0; k < 24; k++) u = norm(mul(C, u));
      // deflate, then repeat for the second axis
      const D = C.map((row, i) => row.map((val, j) => {
        let lam = 0;
        for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) lam += u[a]*C[a][b]*u[b];
        return val - lam*u[i]*u[j];
      }));
      let v = norm([0.2, 1, 0.4]);
      for (let k = 0; k < 24; k++) v = norm(mul(D, v));
      // orthogonalise v against u
      const dot = u[0]*v[0] + u[1]*v[1] + u[2]*v[2];
      v = norm([v[0]-dot*u[0], v[1]-dot*u[1], v[2]-dot*u[2]]);
      return { c, u, v };
    }

    function renderBlockInspector(host, block, caption) {
      const G = blockLocalGeometry(block);
      if (!G) { host.textContent = caption; return; }
      const { c, u, v } = principalPlane(G.pts);

      const W = 208, H = 150, PAD = 16;
      const proj = {};
      let minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
      G.pts.forEach(p => {
        const d = [p.pos[0]-c[0], p.pos[1]-c[1], p.pos[2]-c[2]];
        const x = d[0]*u[0] + d[1]*u[1] + d[2]*u[2];
        const y = d[0]*v[0] + d[1]*v[1] + d[2]*v[2];
        proj[p.id] = [x, y];
        minx = Math.min(minx, x); maxx = Math.max(maxx, x);
        miny = Math.min(miny, y); maxy = Math.max(maxy, y);
      });
      const spanx = Math.max(maxx - minx, 0.8), spany = Math.max(maxy - miny, 0.8);
      const k = Math.min((W - 2*PAD) / spanx, (H - 2*PAD) / spany);
      const X = x => PAD + (x - minx) * k + ((W - 2*PAD) - spanx*k) / 2;
      const Y = y => H - PAD - (y - miny) * k - ((H - 2*PAD) - spany*k) / 2;

      const esc = t => String(t).replace(/[&<>]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[ch]));
      let svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" aria-hidden="true">';
      // bonds first, so atoms sit on top
      G.internal.forEach(([a, b]) => {
        const pa = proj[currentData.atoms[a].id], pb = proj[currentData.atoms[b].id];
        if (!pa || !pb) return;
        svg += '<line x1="' + X(pa[0]).toFixed(1) + '" y1="' + Y(pa[1]).toFixed(1) +
               '" x2="' + X(pb[0]).toFixed(1) + '" y2="' + Y(pb[1]).toFixed(1) +
               '" stroke="#8a8f98" stroke-width="1.6" stroke-linecap="round"/>';
      });
      G.pts.forEach(p => {
        const q = proj[p.id];
        const col = '#' + ('000000' + elementColor(p.el).toString(16)).slice(-6);
        const isMetal = METALS.has(p.el);
        svg += '<circle cx="' + X(q[0]).toFixed(1) + '" cy="' + Y(q[1]).toFixed(1) +
               '" r="' + (isMetal ? 6.2 : 4.2) + '" fill="' + col +
               '" stroke="rgba(0,0,0,.35)" stroke-width="0.8"/>';
        if (isMetal || G.pts.length <= 14) {
          svg += '<text x="' + X(q[0]).toFixed(1) + '" y="' + (Y(q[1]) - 8).toFixed(1) +
                 '" font-size="7.5" text-anchor="middle" fill="currentColor" opacity="0.75">' +
                 esc(p.el) + '</text>';
        }
      });
      svg += '</svg>';

      host.innerHTML =
        '<div class="bi-title">' + esc(caption) + '</div>' +
        '<div class="bi-svg">' + svg + '</div>' +
        '<div class="bi-foot">' + G.pts.length + ' atoms &middot; ' +
        G.internal.length + ' internal bonds &middot; ' +
        G.leaving.length + ' bonds leaving to other blocks' +
        '<span>projected onto the block&rsquo;s two widest directions</span></div>';
    }

    function init(canvasEl, containerEl, labelsLayerEl, hoverTipEl) {
      canvas = canvasEl; container = containerEl; labelsLayer = labelsLayerEl; hoverTip = hoverTipEl;

      scene = new THREE.Scene();
      // powerPreference:'low-power' + capped pixel ratio keep several
      // panels on one page well within the browser's WebGL budget.
      renderer = new THREE.WebGLRenderer({
        canvas, antialias: true, alpha: true,
        powerPreference: 'low-power', failIfMajorPerformanceCaveat: false,
      });
      if (renderer.setPixelRatio && typeof window !== 'undefined') {
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
      }
      camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);

      rotGroup = new THREE.Group(); scene.add(rotGroup);
      atomGroup = new THREE.Group(); rotGroup.add(atomGroup);
      bondGroup = new THREE.Group(); rotGroup.add(bondGroup);
      blockGroup = new THREE.Group(); rotGroup.add(blockGroup);
      cellGroup = new THREE.Group(); rotGroup.add(cellGroup);

      // three lights: a soft sky/ground fill, a key light and a weaker rim light from behind,
      // so the spheres read as round and glossy rather than flat discs
      if (THREE.HemisphereLight) scene.add(new THREE.HemisphereLight(0xffffff, 0x8a93a6, 0.55));
      else scene.add(new THREE.AmbientLight(0xffffff, 0.6));
      scene.add(new THREE.AmbientLight(0xffffff, 0.18));
      const light1 = new THREE.DirectionalLight(0xffffff, 0.95);
      light1.position.set(1, 1.2, 1);
      scene.add(light1);
      const light2 = new THREE.DirectionalLight(0xdfe8ff, 0.35);
      light2.position.set(-1, -0.4, -1.2);
      scene.add(light2);

      sphereGeo = new THREE.SphereGeometry(1, 32, 24);
      cylGeo = new THREE.CylinderGeometry(0.07, 0.07, 1, 8);
      // cloud bonds: a half-bond tube, wider at the atom (bottom) than at the middle (top), and a sheath
      bandGeo = new THREE.CylinderGeometry(0.105, 0.165, 1, 20, 1, true);
      blockGeoSphere = new THREE.SphereGeometry(1, 24, 18);
      blockGeoBox = new THREE.BoxGeometry(1, 1, 1);
      sharedGeos = new Set([sphereGeo, cylGeo, blockGeoSphere, blockGeoBox, bandGeo]);

      centerAll = new THREE.Vector3();

      canvas.addEventListener('mousedown', e => {
        dragging = true; lastX = e.clientX; lastY = e.clientY; dragMoved = 0;
        canvas.style.cursor = 'grabbing';
      });
      window.addEventListener('mouseup', () => { dragging = false; canvas.style.cursor = 'grab'; });
      window.addEventListener('mousemove', e => {
        if (!dragging) return;
        camYaw += (e.clientX - lastX) * 0.006;
        camPitch = Math.max(-1.4, Math.min(1.4, camPitch + (e.clientY - lastY) * 0.006));
        dragMoved += Math.abs(e.clientX - lastX) + Math.abs(e.clientY - lastY);
        lastX = e.clientX; lastY = e.clientY;
        updateCamera();
      });
      canvas.addEventListener('wheel', e => {
        e.preventDefault();
        camDist = Math.max(4, Math.min(160, camDist + e.deltaY * 0.02));
        updateCamera();
      }, { passive: false });
      canvas.addEventListener('touchstart', e => { if (e.touches.length === 1) touchLast = e.touches[0]; });
      canvas.addEventListener('touchmove', e => {
        if (e.touches.length === 1 && touchLast) {
          const t = e.touches[0];
          camYaw += (t.clientX - touchLast.clientX) * 0.006;
          camPitch = Math.max(-1.4, Math.min(1.4, camPitch + (t.clientY - touchLast.clientY) * 0.006));
          touchLast = t;
          updateCamera();
          e.preventDefault();
        }
      }, { passive: false });
      canvas.addEventListener('touchend', () => { touchLast = null; });

      if (hoverTip) {
        canvas.addEventListener('mousemove', e => {
          if (dragging || !currentData) { hoverTip.style.display = 'none'; return; }
          const rect = canvas.getBoundingClientRect();
          mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
          mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
          raycaster.setFromCamera(mouse, camera);
          const targets = [];
          if (atomGroup.visible) targets.push(...atomMeshes);
          if (blockGroup.visible) targets.push(...blockMeshes);
          if (bondGroup.visible) targets.push(...bondMeshes);
          const atomHits = atomGroup.visible ? raycaster.intersectObjects(atomMeshes) : [];
          const hits = atomHits.length ? atomHits : raycaster.intersectObjects(targets);
          if (hits.length === 0) { hoverTip.style.display = 'none'; return; }
          const obj = hits[0].object;
          let text = '';
          let inspect = null;
          if (obj.userData.block) {
            const b = obj.userData.block;
            const comp = Object.entries(b.composition).map(([el, n]) => el + n).join(' ');
            text = (b.type === 'metal' ? 'Node/metal block #' : 'Linker block #') + b.id + ' — ' + b.n_atoms + ' atoms (' + comp + ') — ' + b.n_connections + ' connections';
            // Once the structure has been coarse-grained, a block is drawn as a
            // single sphere and the atoms inside it are no longer on screen at
            // all. That is the point of coarse-graining, and it is also the
            // moment a reader loses track of what a vertex represents. So when
            // the atoms are hidden, the tooltip draws them: the block's own
            // atoms and the bonds between them, projected flat.
            if (!atomGroup.visible) inspect = b;
          } else if (obj.userData.bondInfo) {
            const bi = obj.userData.bondInfo;
            text = 'Bond ' + bi.label + (bi.interblock ? ' — cut by this stage’s algorithm' : ' — intra-block') + ' — ' + bi.length.toFixed(2) + ' Å';
          } else if (obj.userData.atom) {
            const a = obj.userData.atom;
            text = a.el + a.id + (obj.userData.classLabel ? ' — ' + obj.userData.classLabel : '') + ' — click for its properties';
          }
          if (inspect) { renderBlockInspector(hoverTip, inspect, text); }
          else { hoverTip.textContent = text; }
          hoverTip.style.display = 'block';
          hoverTip.style.left = (e.clientX - rect.left + 14) + 'px';
          hoverTip.style.top = (e.clientY - rect.top + 14) + 'px';
        });
        canvas.addEventListener('mouseleave', () => { hoverTip.style.display = 'none'; });
      }

      // ---- click an atom (or a block in the net view) to see its properties ----
      try { if (typeof getComputedStyle !== 'undefined' && getComputedStyle(container).position === 'static') container.style.position = 'relative'; } catch (e) { /* ignore */ }
      infoCard = document.createElement('div');
      infoCard.className = 'atom-card';
      infoCard.setAttribute('role', 'dialog');
      infoCard.setAttribute('aria-label', 'Properties of the selected atom');
      infoCard.style.display = 'none';
      container.appendChild(infoCard);
      styleBar = document.createElement('div');
      styleBar.className = 'atom-stylebar';
      container.appendChild(styleBar);
      drawStyleBar();
      canvas.addEventListener('click', e => {
        if (dragMoved > 6 || !currentData) return;
        const rect = canvas.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const ah = atomGroup.visible ? raycaster.intersectObjects(atomMeshes) : [];
        if (ah.length) { selectAtom(ah[0].object.userData.atom.id); return; }
        const bh = blockGroup.visible ? raycaster.intersectObjects(blockMeshes) : [];
        if (bh.length && (currentOpts.netOnly || !atomGroup.visible)) { selectBlock(bh[0].object.userData.block); return; }
        clearSelection();
      });
      _allRenderers.push(api);

      sizeRenderer();
      window.addEventListener('resize', sizeRenderer);
      if (typeof ResizeObserver !== 'undefined') new ResizeObserver(sizeRenderer).observe(container);

      initContextGuards();

      // Register with the ONE shared ticker (instead of starting our own
      // uncapped per-instance rAF loop, which is what used to exhaust the
      // browser's WebGL contexts and blank the canvases).
      _instances.push({ _frame: _frame });
      _startTicker();
      requestRender();
    }

    // ---- WebGL robustness: pause when off-screen, recover if the browser
    //      drops our context (which otherwise leaves a permanently blank
    //      canvas with no error message anywhere). ----
    function initContextGuards() {
      // 1. Don't render panels the user can't currently see.
      if (typeof IntersectionObserver !== 'undefined') {
        const io = new IntersectionObserver(entries => {
          entries.forEach(en => {
            const nowVisible = en.isIntersecting;
            if (nowVisible && !isVisible) requestRender();  // redraw on re-entry
            isVisible = nowVisible;
          });
        }, { rootMargin: '120px' });
        io.observe(container);
      }

      // 2. If the GPU/browser drops this context, catch it and rebuild.
      if (canvas.addEventListener) {
        canvas.addEventListener('webglcontextlost', ev => {
          // preventDefault() is REQUIRED -- without it the context can
          // never be restored and the canvas stays blank forever.
          if (ev.preventDefault) ev.preventDefault();
          contextLost = true;
        }, false);

        canvas.addEventListener('webglcontextrestored', () => {
          contextLost = false;
          // Rebuild all GPU-side resources, then redraw the last scene.
          try {
            sphereGeo = new THREE.SphereGeometry(1, 32, 24);
            cylGeo = new THREE.CylinderGeometry(0.07, 0.07, 1, 8);
            bandGeo = new THREE.CylinderGeometry(0.105, 0.165, 1, 20, 1, true);
            blockGeoSphere = new THREE.SphereGeometry(1, 24, 18);
            blockGeoBox = new THREE.BoxGeometry(1, 1, 1);
            sharedGeos = new Set([sphereGeo, cylGeo, blockGeoSphere, blockGeoBox, bandGeo]);
            sizeRenderer();
            if (currentData) load(currentData, currentOpts);
          } catch (e) { /* leave the panel blank rather than throwing */ }
        }, false);
      }

      // 3. Stop rendering entirely while the tab is in the background.
      if (typeof document !== 'undefined' && document.addEventListener) {
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden) requestRender();
        });
      }
    }

    function updateLabels() {
      if (!currentData) return;
      const w = container.clientWidth, h = container.clientHeight;
      blockMeshes.forEach(m => {
        const el = m.userData.labelEl;
        if (!el) return;
        const s = worldToScreen(m.position, w, h);
        if (s.behind || !blockGroup.visible) { el.style.display = 'none'; return; }
        el.style.display = 'block';
        el.style.left = s.x + 'px'; el.style.top = s.y + 'px';
      });
    }

    function colorForAtom(atom, opts, blockById) {
      if (opts.colorMode === 'metalNonmetal') {
        return METALS.has(atom.el) ? METAL_COLOR : NONMETAL_COLOR;
      }
      if (opts.colorMode === 'block') {
        const blk = blockById[atom.block];
        // 'custom': caller supplies an explicit {blockId: 0xRRGGBB} map, used by
        // the network page to colour by coordination number or centrality.
        if (opts.blockColorStyle === 'custom' && opts.blockColors) {
          const c = opts.blockColors[blk.id];
          return c === undefined ? 0x8a8f9a : c;
        }
        if (opts.blockColorStyle === 'nodeLinker') {
          return blk.type === 'metal' ? NODE_COLOR : LINKER_COLOR;
        }
        return BLOCK_PALETTE[blk.id % BLOCK_PALETTE.length];
      }
      return elementColor(atom.el);   // 'element' default
    }

    function load(DATA, opts) {
      opts = Object.assign({ colorMode: 'element', showBonds: true, showCell: true, netOnly: false, blockColorStyle: 'nodeLinker' }, opts || {});
      currentData = DATA; currentOpts = opts;
      if (selected) { selected = null; if (infoCard) infoCard.style.display = 'none'; }

      disposeGroup(atomGroup); disposeGroup(bondGroup); disposeGroup(blockGroup); disposeGroup(cellGroup);
      labelsLayer.innerHTML = '';
      atomMeshes = []; bondMeshes = []; blockMeshes = [];

      const blockById = {};
      DATA.blocks.forEach(b => { blockById[b.id] = b; });

      // ---- camera framing ----
      centerAll = new THREE.Vector3();
      DATA.atoms.forEach(a => centerAll.add(new THREE.Vector3(...a.pos)));
      centerAll.divideScalar(DATA.atoms.length);
      let maxExtent = 1;
      DATA.atoms.forEach(a => { maxExtent = Math.max(maxExtent, new THREE.Vector3(...a.pos).distanceTo(centerAll)); });
      camDist = Math.max(16, Math.min(90, maxExtent * (opts.netOnly ? 1.6 : 2.2)));
      updateCamera();

      atomGroup.visible = !opts.netOnly;
      bondGroup.visible = !opts.netOnly && opts.showBonds;
      blockGroup.visible = true;

      if (!opts.netOnly) {
        // ---- real atoms ----
        DATA.atoms.forEach(atom => {
          const r = elementRadius(atom.el);
          const color = colorForAtom(atom, opts, blockById);
          const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.3, metalness: METALS.has(atom.el) ? 0.35 : 0.05 });
          const mesh = new THREE.Mesh(sphereGeo, mat);
          mesh.scale.setScalar(r);
          atom._color = color;
          mesh.position.set(...atom.pos);
          const blk = blockById[atom.block];
          mesh.userData = { atom, classLabel: (opts.colorMode === 'metalNonmetal') ? (METALS.has(atom.el) ? 'metal' : 'nonmetal') : (blk ? (blk.type === 'metal' ? 'node block #' + blk.id : 'linker block #' + blk.id) : '') };
          mesh.userData._r = r;
          atomGroup.add(mesh);
          atomMeshes.push(mesh);
        });

        // ---- bonds ----
        if (opts.showBonds) {
          DATA.bonds.forEach(bd => {
            const a = DATA.atoms[bd.a], b = DATA.atoms[bd.b];
            const pa = new THREE.Vector3(...a.pos), pb = new THREE.Vector3(...b.pos);
            const vec = new THREE.Vector3(...bd.vec);
            const cut = bd.interblock;
            const fixed = bd.highlight !== undefined ? bd.highlight : (cut ? 0x2ec4d6 : null);
            const bondInfo = { label: a.el + a.id + '–' + b.el + b.id, interblock: cut, length: vec.length(), a: bd.a, b: bd.b };
            let parts;
            if (BOND_STYLE === 'cloud') {
              // each half takes its own atom's colour (lightened), or the stage's highlight colour
              const ca = fixed !== null ? fixed : hexMix(a._color !== undefined ? a._color : elementColor(a.el), 0xffffff, 0.18);
              const cb = fixed !== null ? fixed : hexMix(b._color !== undefined ? b._color : elementColor(b.el), 0xffffff, 0.18);
              parts = [makeBand(pa, vec.clone().multiplyScalar(0.5), ca, 1), makeBand(pb, vec.clone().multiplyScalar(-0.5), cb, 1),
                       makeSheath(pa, vec, fixed !== null ? fixed : hexMix(ca, cb, 0.5))];
            } else {
              const color = fixed !== null ? fixed : 0x9a9a9a;
              parts = [makeStub(pa, vec.clone().multiplyScalar(0.5), color), makeStub(pb, vec.clone().multiplyScalar(-0.5), color)];
            }
            parts.forEach(m => { if (m) { m.userData = { bondInfo }; bondGroup.add(m); bondMeshes.push(m); } });
          });
        }
      }

      // ---- block centroid markers (always built; shown fully in netOnly mode,
      //      hidden/near-invisible otherwise except as click/hover targets) ----
      DATA.blocks.forEach(b => {
        const isMetal = b.type === 'metal';
        // blockMarkersFilter: used by the metal-oxo walkthrough's "collapse"
        // steps to reveal only linker markers first, then node markers too --
        // mirroring the real code's order (CollapseLinkers() runs before
        // CollapseNodes()). Undefined/'all' = no filtering (every other
        // caller, e.g. the 7-stage pipeline viewer, is unaffected).
        const filter = opts.blockMarkersFilter;
        if (filter && filter !== 'all' && ((filter === 'node') !== isMetal)) return;
        const color = (opts.blockColorStyle === 'custom' && opts.blockColors && opts.blockColors[b.id] !== undefined)
          ? opts.blockColors[b.id]
          : (opts.blockColorStyle === 'nodeLinker' ? (isMetal ? NODE_COLOR : LINKER_COLOR) : BLOCK_PALETTE[b.id % BLOCK_PALETTE.length]);
        const shownOpacity = opts.netOnly ? 0.95 : (opts.showBlockMarkers ? 0.4 : 0);
        const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.15, transparent: true, opacity: shownOpacity });
        const size = opts.netOnly ? (isMetal ? 0.55 : 0.4) : (isMetal ? 0.95 : 1.5);
        const mesh = new THREE.Mesh(isMetal ? blockGeoSphere : blockGeoBox, mat);
        mesh.scale.setScalar(size);
        mesh.position.set(...b.centroid);
        mesh.userData = { block: b };
        blockGroup.add(mesh);
        blockMeshes.push(mesh);
        if (opts.netOnly) {
          const el = makeLabelEl((isMetal ? 'M' : 'L') + b.id, 'block-label');
          el.style.fontSize = '11px'; el.style.fontWeight = '500';
          mesh.userData.labelEl = el;
        }
      });

      // ---- net-only edges: one line per pair of blocks connected by >=1 interblock bond ----
      if (opts.netOnly) {
        const seenPairs = new Set();
        DATA.bonds.forEach(bd => {
          if (!bd.interblock) return;
          const bi = DATA.atoms[bd.a].block, bj = DATA.atoms[bd.b].block;
          const key = Math.min(bi, bj) + '-' + Math.max(bi, bj);
          if (seenPairs.has(key)) return;
          seenPairs.add(key);
          const cA = blockById[bi].centroid, cB = blockById[bj].centroid;
          const geo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...cA), new THREE.Vector3(...cB)]);
          const mat = new THREE.LineBasicMaterial({ color: 0x9a9a9a, transparent: true, opacity: 0.8 });
          bondGroup.add(new THREE.LineSegments(geo, mat));
        });
        bondGroup.visible = true;
      }

      // ---- unit cell ----
      if (opts.showCell) {
        const M = DATA.cell_matrix;
        const av = new THREE.Vector3(...M[0]), bv = new THREE.Vector3(...M[1]), cv = new THREE.Vector3(...M[2]);
        const O = new THREE.Vector3(0, 0, 0);
        const corners = {
          '000': O, '100': av.clone(), '010': bv.clone(), '001': cv.clone(),
          '110': av.clone().add(bv), '101': av.clone().add(cv), '011': bv.clone().add(cv),
          '111': av.clone().add(bv).add(cv),
        };
        const edges = [
          ['000','100'], ['000','010'], ['000','001'],
          ['100','110'], ['100','101'],
          ['010','110'], ['010','011'],
          ['001','101'], ['001','011'],
          ['110','111'], ['101','111'], ['011','111'],
        ];
        const pts = [];
        edges.forEach(([p1, p2]) => { pts.push(corners[p1], corners[p2]); });
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const mat = new THREE.LineBasicMaterial({ color: 0xbbbbbb, transparent: true, opacity: 0.45 });
        cellGroup.add(new THREE.LineSegments(geo, mat));
      }
      cellGroup.visible = opts.showCell;
      requestRender();   // one redraw for the new scene, then idle again
    }

    function drawStyleBar() {
      if (!styleBar) return;
      styleBar.innerHTML = '<span>Bonds</span>' + ['cloud', 'stick'].map(k =>
        '<button type="button" data-style="' + k + '" aria-pressed="' + (BOND_STYLE === k) + '">' + (k === 'cloud' ? 'Cloud' : 'Stick') + '</button>').join('') +
        '<span class="hint">Click an atom</span>';
      styleBar.querySelectorAll('button').forEach(btn => btn.addEventListener('click', ev => {
        ev.stopPropagation();
        BOND_STYLE = btn.getAttribute('data-style');
        try { localStorage.setItem('mofBondStyle', BOND_STYLE); } catch (e2) { /* ignore */ }
        _allRenderers.forEach(r => r._restyle());           // every 3D view on the page follows
      }));
    }
    function _restyle() { drawStyleBar(); if (currentData) { const keep = selected; load(currentData, currentOpts); if (keep && keep.kind === 'atom') selectAtom(keep.id); } }

    function setGlow(mesh, on) {
      if (!mesh || !mesh.material) return;
      if (mesh.material.emissive && mesh.material.emissive.setHex) mesh.material.emissive.setHex(on ? 0x553300 : 0x000000);
      if (mesh.userData && mesh.userData._r) mesh.scale.setScalar(mesh.userData._r * (on ? 1.22 : 1));
    }
    function clearSelection() {
      if (selected && selected.meshes) selected.meshes.forEach(m => setGlow(m, false));
      selected = null;
      if (infoCard) infoCard.style.display = 'none';
      requestRender();
    }
    function esc(t) { return String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
    function f(x, d) { return (Math.round(x * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d); }
    function fracOf(pos) {
      const M = currentData.cell_matrix;            // rows are a, b, c: pos = u M
      const det = M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0]) + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]);
      const inv = [
        [(M[1][1] * M[2][2] - M[1][2] * M[2][1]) / det, (M[0][2] * M[2][1] - M[0][1] * M[2][2]) / det, (M[0][1] * M[1][2] - M[0][2] * M[1][1]) / det],
        [(M[1][2] * M[2][0] - M[1][0] * M[2][2]) / det, (M[0][0] * M[2][2] - M[0][2] * M[2][0]) / det, (M[0][2] * M[1][0] - M[0][0] * M[1][2]) / det],
        [(M[1][0] * M[2][1] - M[1][1] * M[2][0]) / det, (M[0][1] * M[2][0] - M[0][0] * M[2][1]) / det, (M[0][0] * M[1][1] - M[0][1] * M[1][0]) / det]];
      return [0, 1, 2].map(j => pos[0] * inv[0][j] + pos[1] * inv[1][j] + pos[2] * inv[2][j]);
    }
    // Everything the page knows about one atom: the element's properties, where the atom is,
    // what it is bonded to, and which building block the current stage puts it in.
    function atomInfo(id) {
      const D = currentData, a = D.atoms[id], E = ELEMENTS[a.el] || [a.el, null, null, null, 'element', null, null];
      const nb = [];
      D.bonds.forEach(bd => {
        if (bd.a === id || bd.b === id) {
          const other = bd.a === id ? bd.b : bd.a, o = D.atoms[other];
          nb.push({ id: other, el: o.el, d: Math.hypot(bd.vec[0], bd.vec[1], bd.vec[2]), cut: !!bd.interblock, image: !!bd.cross });
        }
      });
      nb.sort((x, y) => x.d - y.d);
      const blk = D.blocks.filter(b => b.id === a.block)[0];
      return { atom: a, name: E[0], Z: E[1], mass: E[2], en: E[3], kind: E[4], group: E[5], period: E[6],
               cov: COVR[a.el], metal: METALS.has(a.el), neighbours: nb, block: blk, frac: fracOf(a.pos) };
    }
    function selectAtom(id) {
      clearSelection();
      const I = atomInfo(id), a = I.atom;
      const meshes = atomMeshes.filter(m => m.userData.atom && m.userData.atom.id === id);
      bondMeshes.forEach(m => { const bi = m.userData.bondInfo; if (bi && (bi.a === id || bi.b === id)) meshes.push(m); });
      meshes.forEach(m => { if (m.userData.atom) m.userData._r = m.userData._r || m.scale._s || elementRadius(a.el); setGlow(m, true); });
      selected = { kind: 'atom', id, meshes };
      const comp = I.block ? Object.entries(I.block.composition).map(([el, n]) => el + (n > 1 ? '<sub>' + n + '</sub>' : '')).join('') : '';
      const role = I.block ? (I.block.type === 'metal' ? 'node (metal) block #' : 'linker block #') + I.block.id + ' (' + comp + ', ' + I.block.n_atoms + ' atoms, ' + I.block.n_connections + ' connections)' : '—';
      const nbRows = I.neighbours.slice(0, 8).map(n => '<tr><td>' + esc(n.el + n.id) + '</td><td>' + f(n.d, 3) + ' Å</td><td>' + (n.cut ? 'cut at this stage' : (n.image ? 'to the next cell' : '')) + '</td></tr>').join('');
      infoCard.innerHTML =
        '<button type="button" class="close" aria-label="Close">×</button>' +
        '<div class="head"><span class="sym" style="background:' + hexCss(elementColor(a.el)) + '">' + esc(a.el) + '</span><div><b>' + esc(I.name) + '</b> ' + esc(a.el + a.id) +
        '<div class="sub">' + esc(I.kind) + (I.group ? ', group ' + I.group : '') + (I.period ? ', period ' + I.period : '') + '</div></div></div>' +
        '<table class="props">' +
        '<tr><td>Atomic number</td><td>' + (I.Z || '—') + '</td></tr>' +
        '<tr><td>Atomic mass</td><td>' + (I.mass ? I.mass + ' u' : '—') + '</td></tr>' +
        '<tr><td>Electronegativity</td><td>' + (I.en !== null && I.en !== undefined ? f(I.en, 2) : '—') + '</td></tr>' +
        '<tr><td>Covalent radius (bonding)</td><td>' + (I.cov ? f(I.cov, 2) + ' Å' : '—') + '</td></tr>' +
        '<tr><td>Treated as a metal</td><td>' + (I.metal ? 'yes' : 'no') + '</td></tr>' +
        '<tr><td>Bonds (coordination)</td><td>' + I.neighbours.length + '</td></tr>' +
        '<tr><td>Position (Å)</td><td>' + a.pos.map(x => f(x, 2)).join(', ') + '</td></tr>' +
        '<tr><td>Fractional (x, y, z)</td><td>' + I.frac.map(x => f(x, 4)).join(', ') + '</td></tr>' +
        '<tr><td>Building block</td><td>' + role + '</td></tr>' +
        '</table>' +
        (nbRows ? '<div class="nbh">Bonded to</div><table class="nb">' + nbRows + '</table>' + (I.neighbours.length > 8 ? '<div class="sub">and ' + (I.neighbours.length - 8) + ' more</div>' : '') : '');
      infoCard.style.display = 'block';
      infoCard.querySelector('.close').addEventListener('click', ev => { ev.stopPropagation(); clearSelection(); });
      requestRender();
      return I;
    }
    function selectBlock(b) {
      clearSelection();
      const meshes = blockMeshes.filter(m => m.userData.block === b);
      selected = { kind: 'block', id: b.id, meshes };
      const comp = Object.entries(b.composition).map(([el, n]) => el + (n > 1 ? '<sub>' + n + '</sub>' : '')).join('');
      infoCard.innerHTML = '<button type="button" class="close" aria-label="Close">×</button>' +
        '<div class="head"><span class="sym" style="background:' + (b.type === 'metal' ? '#c0392b' : '#2e86c1') + '">' + (b.type === 'metal' ? 'M' : 'L') + '</span><div><b>' +
        (b.type === 'metal' ? 'Node (metal) block' : 'Linker block') + ' #' + b.id + '</b><div class="sub">one vertex of the network</div></div></div>' +
        '<table class="props"><tr><td>Atoms</td><td>' + b.n_atoms + ' (' + comp + ')</td></tr><tr><td>Connections</td><td>' + b.n_connections + '</td></tr>' +
        '<tr><td>Centre (Å)</td><td>' + b.centroid.map(x => f(x, 2)).join(', ') + '</td></tr></table>';
      infoCard.style.display = 'block';
      infoCard.querySelector('.close').addEventListener('click', ev => { ev.stopPropagation(); clearSelection(); });
      requestRender();
    }

    function resize() { sizeRenderer(); }

    const api = { init, load, resize, requestRender, selectAtom, clearSelection, atomInfo, _restyle,
                  get bondStyle() { return BOND_STYLE; } };
    return api;
  }

  root.MOFRender = makeRenderer();
  // .create() builds an ADDITIONAL, fully independent renderer instance (own
  // scene/camera/canvas) for pages that need more than one 3D panel at once
  // (e.g. the metal-oxo walkthrough + drawbacks panels living on the same
  // page). The default root.MOFRender singleton above is unaffected and
  // keeps working exactly as before for every existing caller.
  root.MOFRender.create = makeRenderer;
})(typeof window !== 'undefined' ? window : globalThis);
