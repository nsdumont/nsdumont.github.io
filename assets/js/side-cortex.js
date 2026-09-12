// Procedurally drawn cortical column in the spirit of Cajal's Golgi drawings,
// fixed along the left edge of the page. Layers from top to bottom:
//   I    sparse dots under the pial surface
//   II/III dense small pyramidal cells
//   IV   small stellate cells
//   V    large pyramidal cells with long apical dendrites
//   VI   smaller spindle-like cells thinning into white matter
// Motion is deliberately minimal: now and then one neuron darkens briefly and
// fades back. Configure via `side_art.cortex` in _config.yml.
(function () {
  const root = document.querySelector(".side-cortex");
  if (!root) return;

  const W = parseFloat(root.dataset.width) || 200;
  const seedCfg = parseInt(root.dataset.seed, 10) || 0;
  const animate = root.dataset.animate !== "false";
  const pulseInterval = (parseFloat(root.dataset.pulseInterval) || 6) * 1000;
  const NS = "http://www.w3.org/2000/svg";

  // Seeded PRNG so the drawing can be stable across page loads.
  function mulberry32(a) {
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  let rand = Math.random;
  const R = (a, b) => a + rand() * (b - a);
  const RI = (a, b) => Math.floor(R(a, b + 1));

  let neurons = [];

  function el(name, attrs) {
    const e = document.createElementNS(NS, name);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  // A wobbly polyline from (x, y) heading in direction (dx, dy) for `len` px.
  function fibre(x, y, dx, dy, len, wobble, width) {
    const n = Math.max(2, Math.round(len / 10));
    const pts = [[x, y]];
    let px = x,
      py = y;
    const nx = -dy,
      ny = dx; // normal for sideways wobble
    for (let i = 1; i <= n; i++) {
      const t = (len / n) * i;
      const w = R(-wobble, wobble);
      px = x + dx * t + nx * w;
      py = y + dy * t + ny * w;
      pts.push([px, py]);
    }
    return {
      end: [px, py],
      node: el("polyline", {
        points: pts.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" "),
        fill: "none",
        stroke: "currentColor",
        "stroke-width": width,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
      }),
    };
  }

  function group(opacity) {
    const g = el("g", { class: "neuron" });
    g.style.opacity = opacity.toFixed(2);
    return g;
  }

  // Pyramidal cell: triangular soma, apical dendrite rising to `apicalTop`,
  // a few basal dendrites, and a thin descending axon.
  function pyramidal(x, y, s, apicalTop, yMax) {
    const g = group(R(0.35, 0.8));
    // soma: apex at (x, y - 1.1s), base corners at (x ± s, y + 0.6s), rounded bottom
    const apexY = y - s * 1.1;
    const baseY = y + s * 0.6;
    const bottomY = y + s * 0.78;
    g.appendChild(
      el("path", {
        d: `M ${x} ${apexY} Q ${x + s * 0.9} ${y} ${x + s} ${baseY} Q ${x} ${y + s * 0.95} ${x - s} ${baseY} Q ${x - s * 0.9} ${y} ${x} ${apexY} Z`,
        fill: "currentColor",
      })
    );
    // apical dendrite grows from the apex, with oblique branches and a small tuft
    const len = Math.max(12, apexY - apicalTop + R(-15, 5));
    const ap = fibre(x, apexY + 0.5, 0, -1, len, 1.2, s > 6 ? 0.9 : 0.6);
    g.appendChild(ap.node);
    const nBranch = len > 60 ? RI(1, 3) : RI(0, 1);
    for (let i = 0; i < nBranch; i++) {
      const by = apexY - R(0.25, 0.75) * len;
      const dir = rand() < 0.5 ? -1 : 1;
      g.appendChild(fibre(x, by, dir * 0.55, -0.85, R(8, 22), 1, 0.45).node);
    }
    const tuftN = RI(2, 3);
    for (let i = 0; i < tuftN; i++) {
      const dir = (i - (tuftN - 1) / 2) * 0.7;
      g.appendChild(fibre(ap.end[0], ap.end[1], dir, -0.9, R(5, 12), 0.8, 0.4).node);
    }
    // basal dendrites
    const nBasal = RI(2, 4);
    for (let i = 0; i < nBasal; i++) {
      const dx = R(-1, 1);
      const dy = R(0.2, 0.9);
      const m = Math.hypot(dx, dy) || 1;
      // start just inside the soma so the dendrite visibly emerges from it
      g.appendChild(fibre(x + dx * s * 0.6, baseY + s * 0.05, dx / m, dy / m, R(s * 1.5, s * 4), 1, 0.45).node);
    }
    // axon leaves from the bottom of the soma
    const axLen = Math.min(R(15, 70), yMax - bottomY - 5);
    if (axLen > 8) g.appendChild(fibre(x, bottomY - 0.5, R(-0.1, 0.1), 1, axLen, 0.8, 0.35).node);
    return g;
  }

  // Stellate cell: small round soma with short radiating processes.
  function stellate(x, y, r) {
    const g = group(R(0.35, 0.75));
    g.appendChild(el("circle", { cx: x, cy: y, r: r, fill: "currentColor" }));
    const n = RI(3, 5);
    for (let i = 0; i < n; i++) {
      const a = R(0, Math.PI * 2);
      g.appendChild(fibre(x, y, Math.cos(a), Math.sin(a), R(4, 11), 0.7, 0.4).node);
    }
    return g;
  }

  function dot(x, y, r, minOp, maxOp) {
    return el("circle", {
      cx: x.toFixed(1),
      cy: y.toFixed(1),
      r: r.toFixed(2),
      fill: "currentColor",
      opacity: R(minOp == null ? 0.3 : minOp, maxOp == null ? 0.7 : maxOp).toFixed(2),
    });
  }

  function build() {
    rand = seedCfg ? mulberry32(seedCfg) : Math.random;
    root.innerHTML = "";
    neurons = [];

    const top = 4; // start at the very top so the translucent navbar overlays the upper layers
    const H = Math.max(400, window.innerHeight);
    const svg = el("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}` });
    const span = H - top;
    const L = {
      I: [top + 6, top + span * 0.08],
      II: [top + span * 0.08, top + span * 0.34],
      IV: [top + span * 0.34, top + span * 0.46],
      V: [top + span * 0.46, top + span * 0.68],
      VI: [top + span * 0.68, top + span * 0.92],
      WM: [top + span * 0.92, H],
    };
    const margin = 8;
    const X = () => R(margin, W - margin);

    // faint background of vertical fibres running the full depth
    const bg = el("g", { opacity: 0.18 });
    const nFib = Math.round(W / 9);
    for (let i = 0; i < nFib; i++) {
      const x = R(margin, W - margin);
      const y0 = R(L.I[1], L.V[0]);
      bg.appendChild(fibre(x, y0, 0, 1, R(span * 0.3, H - y0), 1.5, 0.35).node);
    }
    svg.appendChild(bg);

    // layer I: scattered dots, drawn larger and darker so they show through the navbar overlay
    const nDots = Math.round((W * (L.I[1] - L.I[0])) / 90);
    for (let i = 0; i < nDots; i++) svg.appendChild(dot(X(), R(L.I[0], L.I[1]), R(1, 2.2), 0.6, 1));

    // layers II/III: many small pyramidal cells
    const nII = Math.round((W * (L.II[1] - L.II[0])) / 800);
    for (let i = 0; i < nII; i++) {
      const y = R(L.II[0] + 6, L.II[1]);
      const g = pyramidal(X(), y, R(3.6, 5.8), L.I[1] + R(-5, 25), H);
      svg.appendChild(g);
      neurons.push(g);
    }
    // scattered granule-like dots throughout II/III and IV
    const nScatter = Math.round((W * (L.IV[1] - L.II[0])) / 300);
    for (let i = 0; i < nScatter; i++) svg.appendChild(dot(X(), R(L.II[0], L.IV[1]), R(0.5, 1.1)));

    // layer IV: dense small stellate cells
    const nIV = Math.round((W * (L.IV[1] - L.IV[0])) / 420);
    for (let i = 0; i < nIV; i++) {
      const g = stellate(X(), R(L.IV[0], L.IV[1]), R(2, 3.2));
      svg.appendChild(g);
      neurons.push(g);
    }

    // layer V: fewer, large pyramidal cells whose apical dendrites reach layer I
    const nV = Math.round((W * (L.V[1] - L.V[0])) / 2300);
    for (let i = 0; i < nV; i++) {
      const y = R(L.V[0] + 8, L.V[1]);
      const g = pyramidal(X(), y, R(7, 11), L.I[1] + R(-5, 40), H);
      svg.appendChild(g);
      neurons.push(g);
    }

    // layer VI: medium cells, thinning toward the bottom
    const nVI = Math.round((W * (L.VI[1] - L.VI[0])) / 1400);
    for (let i = 0; i < nVI; i++) {
      const t = rand();
      const y = L.VI[0] + t * t * (L.VI[1] - L.VI[0]); // denser near the top of the layer
      const g = pyramidal(X(), y, R(4, 6.2), Math.max(L.IV[0], y - R(40, 160)), H);
      svg.appendChild(g);
      neurons.push(g);
    }

    // white matter: a few sparse fibres and dots
    for (let i = 0; i < 6; i++) svg.appendChild(dot(X(), R(L.WM[0], L.WM[1]), R(0.5, 1)));

    root.appendChild(svg);
  }

  // Gentle activity: a few neurons darken, then fade back.
  function pulse(count) {
    if (!neurons.length) return;
    for (let i = 0; i < (count || 1); i++) {
      const g = neurons[Math.floor(Math.random() * neurons.length)];
      g.classList.add("pulse");
      setTimeout(() => g.classList.remove("pulse"), 1200);
    }
  }

  if (animate) {
    setInterval(() => pulse(1), pulseInterval);
    let lastY = window.scrollY;
    let cooldown = false;
    window.addEventListener(
      "scroll",
      function () {
        if (cooldown) return;
        const y = window.scrollY;
        if (Math.abs(y - lastY) < 60) return;
        lastY = y;
        cooldown = true;
        pulse(7);
        setTimeout(() => (cooldown = false), 500);
      },
      { passive: true }
    );
  }

  let resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(build, 150);
  });

  build();
})();
