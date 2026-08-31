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
    let sphereGeo, cylGeo, blockGeoSphere, blockGeoBox, sharedGeos;
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
      el.style.color = '#141414';
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

      scene.add(new THREE.AmbientLight(0xffffff, 0.6));
      const light1 = new THREE.DirectionalLight(0xffffff, 1.05);
      light1.position.set(1, 1.2, 1);
      scene.add(light1);

      sphereGeo = new THREE.SphereGeometry(1, 20, 16);
      cylGeo = new THREE.CylinderGeometry(0.07, 0.07, 1, 8);
      blockGeoSphere = new THREE.SphereGeometry(1, 24, 18);
      blockGeoBox = new THREE.BoxGeometry(1, 1, 1);
      sharedGeos = new Set([sphereGeo, cylGeo, blockGeoSphere, blockGeoBox]);

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
          const hits = raycaster.intersectObjects(targets);
          if (hits.length === 0) { hoverTip.style.display = 'none'; return; }
          const obj = hits[0].object;
          let text = '';
          if (obj.userData.block) {
            const b = obj.userData.block;
            const comp = Object.entries(b.composition).map(([el, n]) => el + n).join(' ');
            text = (b.type === 'metal' ? 'Node/metal block #' : 'Linker block #') + b.id + ' — ' + b.n_atoms + ' atoms (' + comp + ') — ' + b.n_connections + ' connections';
          } else if (obj.userData.bondInfo) {
            const bi = obj.userData.bondInfo;
            text = 'Bond ' + bi.label + (bi.interblock ? ' — cut by this stage’s algorithm' : ' — intra-block') + ' — ' + bi.length.toFixed(2) + ' Å';
          } else if (obj.userData.atom) {
            const a = obj.userData.atom;
            text = a.el + a.id + (obj.userData.classLabel ? ' — ' + obj.userData.classLabel : '');
          }
          hoverTip.textContent = text;
          hoverTip.style.display = 'block';
          hoverTip.style.left = (e.clientX - rect.left + 14) + 'px';
          hoverTip.style.top = (e.clientY - rect.top + 14) + 'px';
        });
        canvas.addEventListener('mouseleave', () => { hoverTip.style.display = 'none'; });
      }

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
            sphereGeo = new THREE.SphereGeometry(1, 20, 16);
            cylGeo = new THREE.CylinderGeometry(0.07, 0.07, 1, 8);
            blockGeoSphere = new THREE.SphereGeometry(1, 24, 18);
            blockGeoBox = new THREE.BoxGeometry(1, 1, 1);
            sharedGeos = new Set([sphereGeo, cylGeo, blockGeoSphere, blockGeoBox]);
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
          const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.05 });
          const mesh = new THREE.Mesh(sphereGeo, mat);
          mesh.scale.setScalar(r);
          mesh.position.set(...atom.pos);
          const blk = blockById[atom.block];
          mesh.userData = { atom, classLabel: (opts.colorMode === 'metalNonmetal') ? (METALS.has(atom.el) ? 'metal' : 'nonmetal') : (blk ? (blk.type === 'metal' ? 'node block #' + blk.id : 'linker block #' + blk.id) : '') };
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
            const color = bd.highlight !== undefined ? bd.highlight : (cut ? 0x2ec4d6 : 0x9a9a9a);
            const bondInfo = { label: a.el + a.id + '–' + b.el + b.id, interblock: cut, length: vec.length() };
            const s1 = makeStub(pa, vec.clone().multiplyScalar(0.5), color);
            const s2 = makeStub(pb, vec.clone().multiplyScalar(-0.5), color);
            if (s1) { s1.userData = { bondInfo }; bondGroup.add(s1); bondMeshes.push(s1); }
            if (s2) { s2.userData = { bondInfo }; bondGroup.add(s2); bondMeshes.push(s2); }
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

    function resize() { sizeRenderer(); }

    return { init, load, resize, requestRender };
  }

  root.MOFRender = makeRenderer();
  // .create() builds an ADDITIONAL, fully independent renderer instance (own
  // scene/camera/canvas) for pages that need more than one 3D panel at once
  // (e.g. the metal-oxo walkthrough + drawbacks panels living on the same
  // page). The default root.MOFRender singleton above is unaffected and
  // keeps working exactly as before for every existing caller.
  root.MOFRender.create = makeRenderer;
})(typeof window !== 'undefined' ? window : globalThis);
