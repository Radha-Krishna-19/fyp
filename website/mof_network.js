// mof_network.js
// Building-block network analysis, in the browser: periodic quotient graph,
// centrality, Laplacian spectrum, and defect simulation.
//
// This is the JS counterpart of code_09_network_analysis.py. It consumes the
// DATA object produced by mof_decompose.js (blocks + bonds + unwrapped atom
// positions) and never touches that engine, so nothing in the existing site
// changes.
//
// THE CENTRAL POINT
// A MOF is infinite. Building the block graph naively -- one edge per pair of
// blocks that happen to share a bond -- silently destroys periodicity: two
// blocks joined by several bonds running in DIFFERENT lattice directions
// collapse into a single edge. UiO-66 is the structure that exposes it: its
// primitive cell holds one Zr6 cluster whose 12 connections all run out to
// periodic images, so the naive graph loses almost all of them (measured: 1) or degenerates into
// a star), when the true answer is 12.
//
// The correct object is the LABELLED QUOTIENT GRAPH: an edge is identified by
// (blockA, blockB, t) where t is the integer lattice translation the bond
// crosses. Two bonds between the same pair of blocks are the same edge only if
// they cross the same translation. This is also exactly what Systre consumes.

(function (root) {
  'use strict';

  // ---------------- linear algebra (small dense symmetric matrices) ----------------

  function invert3(M) {
    const a = M[0][0], b = M[0][1], c = M[0][2];
    const d = M[1][0], e = M[1][1], f = M[1][2];
    const g = M[2][0], h = M[2][1], i = M[2][2];
    const det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
    return [
      [(e * i - f * h) / det, -(b * i - c * h) / det, (b * f - c * e) / det],
      [-(d * i - f * g) / det, (a * i - c * g) / det, -(a * f - c * d) / det],
      [(d * h - e * g) / det, -(a * h - b * g) / det, (a * e - b * d) / det],
    ];
  }

  // Jacobi eigenvalue algorithm for a real symmetric matrix. n is small here
  // (7-36 vertices), so this is instant and avoids pulling in a linear-algebra
  // library. Returns eigenvalues ascending, plus the eigenvectors.
  function jacobiEigen(Ain, maxSweeps) {
    const n = Ain.length;
    const A = Ain.map(r => r.slice());
    let V = [];
    for (let i = 0; i < n; i++) { V.push(new Array(n).fill(0)); V[i][i] = 1; }
    maxSweeps = maxSweeps || 100;

    for (let sweep = 0; sweep < maxSweeps; sweep++) {
      let off = 0;
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) off += A[i][j] * A[i][j];
      if (off < 1e-12) break;
      for (let p = 0; p < n - 1; p++) {
        for (let q = p + 1; q < n; q++) {
          if (Math.abs(A[p][q]) < 1e-14) continue;
          const theta = (A[q][q] - A[p][p]) / (2 * A[p][q]);
          const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
          const c = 1 / Math.sqrt(t * t + 1), s = t * c;
          for (let k = 0; k < n; k++) {
            const akp = A[k][p], akq = A[k][q];
            A[k][p] = c * akp - s * akq;
            A[k][q] = s * akp + c * akq;
          }
          for (let k = 0; k < n; k++) {
            const apk = A[p][k], aqk = A[q][k];
            A[p][k] = c * apk - s * aqk;
            A[q][k] = s * apk + c * aqk;
          }
          for (let k = 0; k < n; k++) {
            const vkp = V[k][p], vkq = V[k][q];
            V[k][p] = c * vkp - s * vkq;
            V[k][q] = s * vkp + c * vkq;
          }
        }
      }
    }
    const pairs = [];
    for (let i = 0; i < n; i++) pairs.push({ value: A[i][i], vector: V.map(r => r[i]) });
    pairs.sort((x, y) => x.value - y.value);
    return { values: pairs.map(p => p.value), vectors: pairs.map(p => p.vector) };
  }

  // ---------------- graph construction ----------------

  // The labelled quotient graph. Edges carry the lattice translation, so a
  // block connected to its own periodic image stays a real connection.
  function buildQuotientGraph(DATA, opts) {
    opts = opts || {};
    const excluded = opts.excludeBlocks ? new Set(opts.excludeBlocks) : null;

    const blocks = DATA.blocks.filter(b => !(excluded && excluded.has(b.id)));
    const idMap = {};                       // original block id -> compact index
    blocks.forEach((b, i) => { idMap[b.id] = i; });

    const atomBlock = {};
    DATA.atoms.forEach(a => { atomBlock[a.id] = a.block; });

    const inv = invert3(DATA.cell_matrix);
    function toFrac(v) {
      return [
        v[0] * inv[0][0] + v[1] * inv[1][0] + v[2] * inv[2][0],
        v[0] * inv[0][1] + v[1] * inv[1][1] + v[2] * inv[2][1],
        v[0] * inv[0][2] + v[1] * inv[1][2] + v[2] * inv[2][2],
      ];
    }

    const seen = new Set();
    const edges = [];
    DATA.bonds.forEach(bd => {
      const ba = atomBlock[bd.a], bb = atomBlock[bd.b];
      if (excluded && (excluded.has(ba) || excluded.has(bb))) return;
      const pa = DATA.atoms[bd.a].pos, pb = DATA.atoms[bd.b].pos;
      // where atom b actually sits, seen from a's unwrapped frame
      const actual = [pa[0] + bd.vec[0], pa[1] + bd.vec[1], pa[2] + bd.vec[2]];
      const delta = [actual[0] - pb[0], actual[1] - pb[1], actual[2] - pb[2]];
      const fr = toFrac(delta);
      const t = [Math.round(fr[0]), Math.round(fr[1]), Math.round(fr[2])];
      if (ba === bb && t[0] === 0 && t[1] === 0 && t[2] === 0) return;   // internal bond

      // canonical orientation: (i,j,t) and (j,i,-t) are one edge
      let i = idMap[ba], j = idMap[bb], tt = t;
      if (j < i || (j === i && (t[0] < 0 || (t[0] === 0 && (t[1] < 0 || (t[1] === 0 && t[2] < 0)))))) {
        const tmp = i; i = j; j = tmp;
        tt = [-t[0], -t[1], -t[2]];
      }
      const key = i + ',' + j + ',' + tt.join('|');
      if (seen.has(key)) return;
      seen.add(key);
      edges.push({ i, j, t: tt });
    });

    return { blocks, edges, n: blocks.length };
  }

  // The naive construction, kept only to demonstrate what it gets wrong.
  function buildNaiveGraph(DATA) {
    const atomBlock = {};
    DATA.atoms.forEach(a => { atomBlock[a.id] = a.block; });
    const idMap = {};
    DATA.blocks.forEach((b, i) => { idMap[b.id] = i; });
    const seen = new Set(), edges = [];
    DATA.bonds.forEach(bd => {
      const i = idMap[atomBlock[bd.a]], j = idMap[atomBlock[bd.b]];
      if (i === j) return;
      const key = Math.min(i, j) + ',' + Math.max(i, j);
      if (seen.has(key)) return;
      seen.add(key);
      edges.push({ i: Math.min(i, j), j: Math.max(i, j), t: [0, 0, 0] });
    });
    return { blocks: DATA.blocks.slice(), edges, n: DATA.blocks.length };
  }

  // ---------------- analysis ----------------

  function degrees(G) {
    const d = new Array(G.n).fill(0);
    G.edges.forEach(e => { d[e.i]++; d[e.j]++; });   // self-loop across t counts twice: correct
    return d;
  }

  function adjacency(G) {
    const A = [];
    for (let i = 0; i < G.n; i++) A.push(new Array(G.n).fill(0));
    G.edges.forEach(e => { A[e.i][e.j] += 1; A[e.j][e.i] += 1; });
    return A;
  }

  function laplacianSpectrum(G) {
    const A = adjacency(G), d = degrees(G);
    const L = A.map((row, i) => row.map((v, j) => (i === j ? d[i] - v : -v)));
    return jacobiEigen(L).values;
  }

  // Eigenvector centrality: principal eigenvector of the adjacency matrix.
  // In a defect-free crystal every symmetry-equivalent block gets an identical
  // value -- that degeneracy is a real property of the structure, not an error,
  // and it is why ranking blocks inside one perfect cell is not meaningful.
  function eigenvectorCentrality(G) {
    if (G.n === 0) return [];
    const A = adjacency(G);
    const { values, vectors } = jacobiEigen(A);
    const principal = vectors[values.length - 1].map(Math.abs);
    const max = Math.max.apply(null, principal) || 1;
    return principal.map(v => v / max);
  }

  // Betweenness: fraction of shortest paths through each vertex (Brandes).
  // Distinguishes blocks that bridge regions from blocks that merely have
  // many neighbours.
  function betweenness(G) {
    const adj = [];
    for (let i = 0; i < G.n; i++) adj.push([]);
    G.edges.forEach(e => { adj[e.i].push(e.j); adj[e.j].push(e.i); });
    const BC = new Array(G.n).fill(0);
    for (let s = 0; s < G.n; s++) {
      const S = [], P = [], sigma = new Array(G.n).fill(0), dist = new Array(G.n).fill(-1);
      for (let i = 0; i < G.n; i++) P.push([]);
      sigma[s] = 1; dist[s] = 0;
      const Q = [s];
      while (Q.length) {
        const v = Q.shift(); S.push(v);
        adj[v].forEach(w => {
          if (dist[w] < 0) { dist[w] = dist[v] + 1; Q.push(w); }
          if (dist[w] === dist[v] + 1) { sigma[w] += sigma[v]; P[w].push(v); }
        });
      }
      const delta = new Array(G.n).fill(0);
      while (S.length) {
        const w = S.pop();
        P[w].forEach(v => { delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w]); });
        if (w !== s) BC[w] += delta[w];
      }
    }
    const norm = G.n > 2 ? ((G.n - 1) * (G.n - 2)) : 1;
    const out = BC.map(v => v / norm);
    const max = Math.max.apply(null, out) || 1;
    return { raw: out, normalised: out.map(v => v / max) };
  }

  function distinctCount(values, dp) {
    const f = Math.pow(10, dp === undefined ? 3 : dp);
    return new Set(values.map(v => Math.round(v * f))).size;
  }

  // Full report for one structure.
  function analyse(DATA, opts) {
    const G = buildQuotientGraph(DATA, opts);
    const deg = degrees(G);
    const ev = eigenvectorCentrality(G);
    const bt = betweenness(G);
    const spec = laplacianSpectrum(G);

    const nodeCN = [], linkerCN = [];
    G.blocks.forEach((b, i) => (b.type === 'metal' ? nodeCN : linkerCN).push(deg[i]));

    return {
      graph: G, degrees: deg, eigenvector: ev, betweenness: bt.normalised,
      spectrum: spec,
      lambda2: spec.length > 1 ? spec[1] : 0,
      lambdaMax: spec.length ? spec[spec.length - 1] : 0,
      nodeCN: Array.from(new Set(nodeCN)).sort((a, b) => a - b),
      linkerCN: Array.from(new Set(linkerCN)).sort((a, b) => a - b),
      distinctCentrality: distinctCount(ev),
      nBlocks: G.n, nEdges: G.edges.length,
    };
  }

  root.MOFNetwork = {
    buildQuotientGraph, buildNaiveGraph, degrees, adjacency,
    laplacianSpectrum, eigenvectorCentrality, betweenness,
    jacobiEigen, analyse, distinctCount,
  };
})(typeof window !== 'undefined' ? window : globalThis);
