// Decorative grid of squares fixed along the left edge of the page.
// Squares are randomly filled; scrolling re-randomizes a subset of them.
// Configure via `side_art.grid` in _config.yml (enable with side_art.mode: grid).
(function () {
  const root = document.querySelector(".side-grid");
  if (!root) return;

  const cols = parseInt(root.dataset.columns, 10) || 5;
  const size = parseFloat(root.dataset.cellSize) || 18;
  const gap = parseFloat(root.dataset.gap) || 5;
  const fillProb = parseFloat(root.dataset.fillProbability) || 0.45;
  const updateFrac = parseFloat(root.dataset.updateFraction) || 0.08;
  const radius = Math.max(2, size * 0.18);
  const step = size + gap;
  const NS = "http://www.w3.org/2000/svg";

  let cells = [];

  function build() {
    root.innerHTML = "";
    const rows = Math.ceil(window.innerHeight / step) + 1;
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("width", cols * step - gap);
    svg.setAttribute("height", rows * step - gap);
    svg.setAttribute("viewBox", `0 0 ${cols * step - gap} ${rows * step - gap}`);
    cells = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const rect = document.createElementNS(NS, "rect");
        rect.setAttribute("x", c * step);
        rect.setAttribute("y", r * step);
        rect.setAttribute("width", size);
        rect.setAttribute("height", size);
        rect.setAttribute("rx", radius);
        rect.setAttribute("ry", radius);
        if (Math.random() < fillProb) rect.classList.add("sg-on");
        svg.appendChild(rect);
        cells.push(rect);
      }
    }
    root.appendChild(svg);
  }

  function shuffleSome() {
    const n = Math.max(1, Math.round(cells.length * updateFrac));
    for (let i = 0; i < n; i++) {
      const rect = cells[Math.floor(Math.random() * cells.length)];
      rect.classList.toggle("sg-on", Math.random() < fillProb);
    }
  }

  // Re-randomize on scroll, at most once per animation frame and only after
  // the page has actually moved a little, so slow scrolls don't flicker.
  let lastY = window.scrollY;
  let ticking = false;
  window.addEventListener(
    "scroll",
    function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        ticking = false;
        const y = window.scrollY;
        if (Math.abs(y - lastY) >= step) {
          lastY = y;
          shuffleSome();
        }
      });
    },
    { passive: true }
  );

  let resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(build, 150);
  });

  build();
})();
