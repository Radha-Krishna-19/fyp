// mof_multifractal.js
// iNMFA — influential-node multifractal analysis, in the browser.
// Browser counterpart of code_10_multifractal_spectrum.py; the two agree.
//
// PIPELINE
//   quotient graph -> supercell -> influential nodes -> box covering
//   -> partition function Z(q,r) -> tau(q) -> Legendre -> alpha, f(alpha)
//
// The four corrections that make this produce a defined spectrum at all are
// documented at each step below; the originating notebook returned NaN for two
// of the four test structures.

(function (root) {
  'use strict';

  // ---- FIX 8: expand the primitive cell so there is a range of box radii to
  // fit a power law across. Every edge already carries its lattice translation,
  // so this is exact: block i in cell c joins block j in cell c + t.
  function supercell(G, n) {
    const K = G.n;
    const cells = [];
    for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) for (let c = 0; c < n; c++) cells.push([a, b, c]);
    const nc = cells.length;
    const id = (bi, ci) => bi * nc + ci;
    const kinds = new Array(K * nc);
    for (let bi = 0; bi < K; bi++) for (let ci = 0; ci < nc; ci++) kinds[id(bi, ci)] = G.blocks[bi].type;

    const adj = [];
    for (let i = 0; i < K * nc; i++) adj.push([]);
    cells.forEach((cell, ci) => {
      G.edges.forEach(e => {
        const t = e.t || [0, 0, 0];
        const tgt = [((cell[0] + t[0]) % n + n) % n, ((cell[1] + t[1]) % n + n) % n, ((cell[2] + t[2]) % n + n) % n];
        let cj = -1;
        for (let k = 0; k < nc; k++) if (cells[k][0] === tgt[0] && cells[k][1] === tgt[1] && cells[k][2] === tgt[2]) { cj = k; break; }
        const u = id(e.i, ci), v = id(e.j, cj);
        adj[u].push(v); adj[v].push(u);
      });
    });
    return { n: K * nc, adj, kinds, supercellN: n };
  }

  function degreesOf(g) { return g.adj.map(a => a.length); }

  // ---- FIX 6: report the tie ambiguity instead of hiding it ----
  function selectInfluential(g, topPercent) {
    const deg = degreesOf(g);
    const k = Math.max(1, Math.ceil(g.n * (topPercent || 0.30)));
    const order = deg.map((d, i) => [i, d]).sort((a, b) => b[1] - a[1]);
    const chosen = order.slice(0, k).map(p => p[0]);
    const cutoff = deg[chosen[chosen.length - 1]];
    const tied = deg.filter(d => d === cutoff).length;
    const above = deg.filter(d => d > cutoff).length;
    return { chosen, info: { k, cutoff, tied, slots: k - above, ambiguous: tied > (k - above),
                             distinct: new Set(deg).size } };
  }

  function bfsAll(g) {
    const N = g.n, dist = [];
    for (let s = 0; s < N; s++) {
      const d = new Int32Array(N).fill(-1);
      d[s] = 0;
      const q = [s];
      for (let h = 0; h < q.length; h++) {
        const u = q[h];
        const nb = g.adj[u];
        for (let x = 0; x < nb.length; x++) if (d[nb[x]] < 0) { d[nb[x]] = d[u] + 1; q.push(nb[x]); }
      }
      dist.push(d);
    }
    return dist;
  }

  function mulberry(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function boxCovering(g, rb, dist, rand) {
    const N = g.n;
    const covered = new Uint8Array(N);
    const nodeBox = new Int32Array(N).fill(-1);
    const boxSize = [];
    const order = [];
    for (let i = 0; i < N; i++) order.push(i);
    for (let i = N - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); const t = order[i]; order[i] = order[j]; order[j] = t; }
    let bid = 0;
    for (let oi = 0; oi < order.length; oi++) {
      const c = order[oi];
      if (covered[c]) continue;
      const d = dist[c];
      let cnt = 0;
      for (let x = 0; x < N; x++) if (!covered[x] && d[x] >= 0 && d[x] <= rb) { covered[x] = 1; nodeBox[x] = bid; cnt++; }
      if (cnt === 0) { covered[c] = 1; nodeBox[c] = bid; cnt = 1; }
      boxSize.push(cnt);
      bid++;
    }
    return { nodeBox, boxSize };
  }

  // ---- FIX 1: box-cover the FULL graph; read the measure at influential nodes.
  // The notebook fed the influential-node INDUCED subgraph here, which in a MOF
  // is edgeless (metal nodes are never bonded to each other), so no distances
  // existed and the spectrum was undefined.
  //
  // Returns PER-TRIAL measures (radii x nTrials x influential), not averaged --
  // see FIX 9 in computeTau. Averaging p(r) across trials here, before it is
  // raised to the power q, is what FIX 9 corrects.
  function probabilityMeasures(g, influential, radii, nTrials, seed, dist) {
    const N = g.n;
    const trials = radii.map(() => []);
    for (let t = 0; t < nTrials; t++) {
      const rand = mulberry(seed + t * 7919);
      radii.forEach((r, ri) => {
        const { nodeBox, boxSize } = boxCovering(g, r, dist, rand);
        const p = influential.map(node => {
          const b = nodeBox[node];
          return b >= 0 ? boxSize[b] / N : 0;
        });
        trials[ri].push(p);
      });
    }
    return trials;   // trials[ri] = array of nTrials arrays, one p-value per influential node
  }

  // FIX 10 -- the paper defines tau(q) = ln P_q / ln(r/r_N), which over several
  // radii is least squares THROUGH THE ORIGIN, because P_q ~ (r/r_N)^tau has no
  // prefactor. A free-intercept slope is a different quantity, and at q = 0 it
  // is catastrophically wrong: every term is pr_i^0 = 1, so P_0 = |I| is the
  // same at every radius; a flat line has slope 0, so tau(0) = 0 and
  // f(alpha_0) = 0. But f(alpha_0) must be D_0, the PEAK -- so the inverted
  // parabola a multifractal spectrum must have collapses into a falling curve.
  // Verified: free-intercept gives tau(0)=0 and no peak; through-origin gives
  // tau(0) = -3.5028, f(0) = +3.5028, peak exactly at q = 0.
  function linfit(x, y, throughOrigin) {
    let n = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (let i = 0; i < x.length; i++) {
      if (!isFinite(x[i]) || !isFinite(y[i])) continue;
      n++; sx += x[i]; sy += y[i]; sxx += x[i] * x[i]; sxy += x[i] * y[i];
    }
    if (n < 2) return NaN;                       // FIX 5: need >= 2 points
    if (throughOrigin !== false) {               // the paper's definition (default)
      return Math.abs(sxx) < 1e-12 ? NaN : sxy / sxx;
    }
    const den = n * sxx - sx * sx;
    if (Math.abs(den) < 1e-12) return NaN;
    return (n * sxy - sx * sy) / den;
  }

  // ---- FIX 9: average ln Z(q,r) over trials, NOT p(r) before exponentiation.
  // Building Z from trial-averaged p values exponentiates an already-smoothed
  // quantity and biases the spectrum narrow -- averaging suppresses exactly the
  // fluctuation multifractality measures. Correct order: form Z per trial, log
  // it, then average the logs before fitting tau(q).
  //
  // Found independently on a separate dataset by a teammate's notebook
  // (mof_multi_block_spectrum.ipynb). Measured on our own HKUST-1 quotient
  // graph, same seeds and same coverings: wrong 0.021 +/- 0.004, correct
  // 0.327 +/- 0.032. Python mirror: code_10_multifractal_spectrum.py FIX 9.
  //
  // `trials` is radii x nTrials x influential (see probabilityMeasures).
  // `wrongOrder` reproduces the old estimator so the site can show the contrast.
  function computeTau(trials, radii, rN, qValues, wrongOrder, tauMode) {
    const thruOrigin = (tauMode !== 'slope');
    const x = radii.map(r => Math.log(r / rN));

    if (wrongOrder) {
      const avg = trials.map(perTrial => {
        const nI = perTrial.length ? perTrial[0].length : 0;
        const a = new Array(nI).fill(0);
        perTrial.forEach(p => { for (let i = 0; i < nI; i++) a[i] += p[i]; });
        return a.map(v => v / (perTrial.length || 1));
      });
      return qValues.map(q => {
        const y = avg.map(row => {
          let Z = 0, any = false;
          for (let i = 0; i < row.length; i++) if (row[i] > 0) { Z += Math.pow(row[i], q); any = true; }
          return any && Z > 0 ? Math.log(Z) : NaN;
        });
        return linfit(x, y, thruOrigin);
      });
    }

    return qValues.map(q => {
      const y = trials.map(perTrial => {
        const logs = [];
        for (let t = 0; t < perTrial.length; t++) {
          const row = perTrial[t];
          let Z = 0, any = false;
          for (let i = 0; i < row.length; i++) if (row[i] > 0) { Z += Math.pow(row[i], q); any = true; }
          if (any && Z > 0) logs.push(Math.log(Z));
        }
        if (!logs.length) return NaN;
        let s = 0; for (let k = 0; k < logs.length; k++) s += logs[k];
        return s / logs.length;
      });
      return linfit(x, y, thruOrigin);
    });
  }

  function gradient(y, x) {
    const n = y.length, out = new Array(n);
    for (let i = 0; i < n; i++) {
      if (i === 0) out[i] = (y[1] - y[0]) / (x[1] - x[0]);
      else if (i === n - 1) out[i] = (y[n - 1] - y[n - 2]) / (x[n - 1] - x[n - 2]);
      else out[i] = (y[i + 1] - y[i - 1]) / (x[i + 1] - x[i - 1]);
    }
    return out;
  }

  function asymmetry(alpha, qValues) {
    const fin = alpha.filter(isFinite);
    if (!fin.length) return NaN;
    let i0 = 0, best = Infinity;
    qValues.forEach((q, i) => { if (Math.abs(q) < best) { best = Math.abs(q); i0 = i; } });
    const a0 = alpha[i0], amin = Math.min.apply(null, fin), amax = Math.max.apply(null, fin);
    const L = a0 - amin, R = amax - a0;
    if (!isFinite(L) || !isFinite(R) || L <= 0 || R <= 0) return NaN;   // FIX 5
    return Math.log(L / R);
  }

  // ---- full analysis for one structure ----
  function analyse(DATA, opts) {
    opts = opts || {};
    const topPercent = opts.topPercent || 0.30;
    const nTrials = opts.nTrials || 24;          // FIX 7: not 5
    const minBlocks = opts.minBlocks || 60;      // FIX 8
    const G = root.MOFNetwork.buildQuotientGraph(DATA);
    let n = 1;
    while (G.n * Math.pow(n, 3) < minBlocks && n < 4) n++;
    const g = n > 1 ? supercell(G, n)
                    : (function () {
                        const adj = []; for (let i = 0; i < G.n; i++) adj.push([]);
                        G.edges.forEach(e => { adj[e.i].push(e.j); adj[e.j].push(e.i); });
                        return { n: G.n, adj, kinds: G.blocks.map(b => b.type), supercellN: 1 };
                      })();

    const sel = selectInfluential(g, topPercent);
    if (!g.adj.some(a => a.length)) {
      return { ok: false, reason: 'graph has no edges', supercellN: g.supercellN, K: g.n };
    }
    const dist = bfsAll(g);
    let diameter = 0;
    for (let i = 0; i < g.n; i++) for (let j = 0; j < g.n; j++) if (dist[i][j] > diameter) diameter = dist[i][j];
    diameter = Math.max(diameter, 2);
    const radii = []; for (let r = 1; r <= diameter; r++) radii.push(r);

    const qValues = []; for (let i = 0; i < 41; i++) qValues.push(-10 + (20 * i) / 40);
    const pr = probabilityMeasures(g, sel.chosen, radii, nTrials, opts.seed || 0, dist);
    const tau = computeTau(pr, radii, diameter, qValues, opts.wrongOrder, opts.tauMode);
    const alpha = gradient(tau, qValues);
    const fAlpha = qValues.map((q, i) => q * alpha[i] - tau[i]);
    const fin = alpha.filter(isFinite);
    return {
      ok: fin.length > 1, K: g.n, supercellN: g.supercellN, radii, qValues, tau, alpha,
      fAlpha, asymmetry: asymmetry(alpha, qValues),
      alphaMin: fin.length ? Math.min.apply(null, fin) : NaN,
      alphaMax: fin.length ? Math.max.apply(null, fin) : NaN,
      width: fin.length ? Math.max.apply(null, fin) - Math.min.apply(null, fin) : NaN,
      influential: sel.chosen, selection: sel.info,
      reason: fin.length > 1 ? '' : 'spectrum undefined',
    };
  }

  // ---- reference band + candidate scoring ----
  function cleanCurve(alpha, fAlpha) {
    const pts = [];
    for (let i = 0; i < alpha.length; i++) if (isFinite(alpha[i]) && isFinite(fAlpha[i])) pts.push([alpha[i], fAlpha[i]]);
    pts.sort((a, b) => a[0] - b[0]);
    const a = [], f = [];
    pts.forEach(p => {
      if (a.length && Math.abs(p[0] - a[a.length - 1]) < 1e-12) { f[f.length - 1] = (f[f.length - 1] + p[1]) / 2; }
      else { a.push(p[0]); f.push(p[1]); }
    });
    return { a, f };
  }

  function interp(grid, a, f) {
    return grid.map(x => {
      if (x < a[0] || x > a[a.length - 1]) return NaN;
      let i = 0; while (i < a.length - 2 && a[i + 1] < x) i++;
      const t = (x - a[i]) / (a[i + 1] - a[i] || 1);
      return f[i] + t * (f[i + 1] - f[i]);
    });
  }

  // NOTE: buildBand() and scoreCandidate() used to live here. They built a
  // reference band from the four demonstration structures and scored a fifth
  // against it. That is not a result -- four structures cannot define a band,
  // and their unit cells are far too small for a trustworthy power-law fit --
  // so the band is computed over the 77-framework dataset in the analysis
  // notebook instead, and this API was deleted rather than left to be called.

  // =================================================================
  // NMFA / iNMFA — BOX-GROWING, exactly as published
  //   Xiao et al., Sci Rep 11, 22964 (2021)
  //   https://www.nature.com/articles/s41598-021-02203-4
  //
  // The paper proposes box-GROWING and explicitly contrasts it with the
  // box-counting/covering family. The difference matters:
  //   box-covering  tile the network with randomly-seeded boxes; a node's
  //                 measure is the size of whichever box covers it -> stochastic
  //   box-growing   centre a box on node i and grow r; the measure is M_i(r),
  //                 the count of nodes within distance r -> DETERMINISTIC
  // Being deterministic, this removes the reproducibility problem entirely.
  //
  //   u_i(r) = M_i(r)/M ,  U_q(r) = SUM u_i^q ,  U_q ~ (r/d)^tau(q)
  //   alpha = dtau/dq , f = q*alpha - tau , D(q) = tau/q
  //   A = ln[(alpha_0 - alpha_min)/(alpha_max - alpha_0)],  alpha_0 = argmax f
  // =================================================================
  function growthCurves(g) {
    const N = g.n, dist = bfsAll(g);
    let dNet = 0;
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) if (dist[i][j] > dNet) dNet = dist[i][j];
    dNet = Math.max(dNet, 2);
    const radii = []; for (let r = 1; r <= dNet; r++) radii.push(r);
    const M = [];
    for (let i = 0; i < N; i++) {
      const counts = new Array(dNet + 1).fill(0);
      for (let j = 0; j < N; j++) { const d = dist[i][j]; if (d > 0 && d <= dNet) counts[d]++; }
      let run = 1; const curve = [];
      for (let k = 0; k < radii.length; k++) { run += counts[radii[k]]; curve.push(run); }
      M.push(curve);
    }
    return { M, radii, dNet, N };
  }

  function nmfaPaper(g, subset) {
    const { M, radii, dNet, N } = growthCurves(g);
    const I = subset && subset.length ? subset : M.map((_c, i) => i);
    const qValues = []; for (let i = 0; i < 41; i++) qValues.push(-10 + (20 * i) / 40);
    const x = radii.map(r => Math.log(r / dNet));
    const tau = qValues.map(q => {
      const y = radii.map((_r, ri) => {
        let Z = 0;
        for (let k = 0; k < I.length; k++) Z += Math.pow(M[I[k]][ri] / N, q);
        return Z > 0 ? Math.log(Z) : NaN;
      });
      // The paper's own method, so always the paper's tau: through the origin.
      return linfit(x, y, true);
    });
    const alpha = gradient(tau, qValues);
    const f = qValues.map((q, i) => q * alpha[i] - tau[i]);
    const Dq = qValues.map((q, i) => (Math.abs(q) > 1e-9 ? tau[i] / q : NaN));
    // alpha_0 = alpha where f(alpha) is maximum (the paper's definition)
    let a0 = NaN, best = -Infinity;
    f.forEach((v, i) => { if (isFinite(v) && isFinite(alpha[i]) && v > best) { best = v; a0 = alpha[i]; } });
    const fin = alpha.filter(isFinite);
    const amin = fin.length ? Math.min.apply(null, fin) : NaN;
    const amax = fin.length ? Math.max.apply(null, fin) : NaN;
    const L = a0 - amin, R = amax - a0;
    const A = (L > 0 && R > 0) ? Math.log(L / R) : NaN;
    // how many DISTINCT growth curves does the measure set contain?
    const distinct = new Set(I.map(i => M[i].join(','))).size;
    return { qValues, tau, alpha, fAlpha: f, Dq, radii, dNet, N,
             alpha0: a0, alphaMin: amin, alphaMax: amax,
             width: isFinite(amax) ? amax - amin : NaN, asymmetry: A,
             nMeasure: I.length, distinctCurves: distinct,
             ok: fin.length > 1 };
  }

  function analysePaper(DATA, opts) {
    opts = opts || {};
    const G = root.MOFNetwork.buildQuotientGraph(DATA);
    let n = 1;
    while (G.n * Math.pow(n, 3) < (opts.minBlocks || 60) && n < 4) n++;
    const g = n > 1 ? supercell(G, n) : (function () {
      const adj = []; for (let i = 0; i < G.n; i++) adj.push([]);
      G.edges.forEach(e => { adj[e.i].push(e.j); adj[e.j].push(e.i); });
      return { n: G.n, adj, kinds: G.blocks.map(b => b.type), supercellN: 1 };
    })();
    const sel = selectInfluential(g, opts.topPercent || 0.10);   // paper uses top 10%
    return { supercellN: g.supercellN, K: g.n,
             nmfa: nmfaPaper(g, null), inmfa: nmfaPaper(g, sel.chosen),
             influential: sel.chosen, selection: sel.info };
  }

  root.MOFMultifractal = { analyse, supercell, selectInfluential,
                           cleanCurve, interp, nmfaPaper, analysePaper, growthCurves };
})(typeof window !== 'undefined' ? window : globalThis);
