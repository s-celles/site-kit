// site-kit charts (SPEC.md §7, §11): a crosshair and a tooltip for the
// inline SVG charts (svg.viz-chart). Points are g.viz-pt with an aria-label
// and a circle.viz-dot.
//
// - A sparse chart: each point is a tab stop; hovering or focusing it shows
//   its label.
// - A dense chart (svg tabindex="0" data-viz="dense"): the chart is one tab
//   stop. The arrow keys step through x (Home and End jump to the ends), and
//   the tooltip lists every series at that x, under the group's data-x-label
//   when the points carry one. The mouse picks the nearest x.
//
// The tooltip stays inside the chart's figure (or its .viz container).
document.addEventListener("DOMContentLoaded", () => {
  const ns = "http://www.w3.org/2000/svg";

  document.querySelectorAll("svg.viz-chart").forEach((svg) => {
    const box = svg.closest("figure, .viz") || svg.parentElement;
    if (getComputedStyle(box).position === "static") box.style.position = "relative";
    const tip = document.createElement("div");
    tip.className = "viz-tooltip";
    tip.setAttribute("role", "status");
    tip.hidden = true;
    box.appendChild(tip);

    const guide = document.createElementNS(ns, "line");
    guide.setAttribute("class", "viz-guide");
    guide.style.display = "none";
    svg.insertBefore(guide, svg.firstChild);
    const grid = svg.querySelectorAll(".viz-grid");
    const top = grid.length ? grid[grid.length - 1].getAttribute("y1") : 0;
    const bottom = grid.length ? grid[0].getAttribute("y1") : svg.viewBox.baseVal.height;

    const pts = [...svg.querySelectorAll("g.viz-pt")];
    pts.forEach((pt) => { const t = pt.querySelector("title"); if (t) t.remove(); });  // the tooltip replaces the native one

    // the points grouped by x, in x order
    const byX = new Map();
    pts.forEach((pt) => {
      const x = parseFloat(pt.querySelector(".viz-dot").getAttribute("cx"));
      if (!byX.has(x)) byX.set(x, []);
      byX.get(x).push(pt);
    });
    const xs = [...byX.keys()].sort((a, b) => a - b);

    const place = (dots, x) => {
      guide.setAttribute("x1", x); guide.setAttribute("x2", x);
      guide.setAttribute("y1", top); guide.setAttribute("y2", bottom);
      guide.style.display = "";
      tip.hidden = false;
      const b = box.getBoundingClientRect();
      const ys = dots.map((d) => d.getBoundingClientRect());
      const cx = ys[0].left + ys[0].width / 2 - b.left;
      const cy = Math.min(...ys.map((r) => r.top)) - b.top - 8;
      const half = tip.offsetWidth / 2;
      tip.style.left = `${Math.max(half, Math.min(b.width - half, cx))}px`;
      tip.style.top = `${Math.max(tip.offsetHeight, cy)}px`;
    };
    const hide = () => { guide.style.display = "none"; tip.hidden = true; };

    if (svg.dataset.viz === "dense") {
      let i = xs.length - 1;
      const show = () => {
        const group = byX.get(xs[i]);
        pts.forEach((p) => p.classList.remove("viz-active"));
        group.forEach((p) => p.classList.add("viz-active"));
        const head = group[0].dataset.xLabel;   // optional: the x value, shown once
        tip.textContent = (head ? [head] : []).concat(group.map((p) => p.getAttribute("aria-label"))).join("\n");
        place(group.map((p) => p.querySelector(".viz-dot")), xs[i]);
      };
      const clear = () => { pts.forEach((p) => p.classList.remove("viz-active")); hide(); };
      pts.forEach((p) => p.removeAttribute("tabindex"));
      svg.addEventListener("focus", show);
      svg.addEventListener("blur", clear);
      svg.addEventListener("keydown", (e) => {
        const step = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 }[e.key];
        if (step) i = Math.max(0, Math.min(xs.length - 1, i + step));
        else if (e.key === "Home") i = 0;
        else if (e.key === "End") i = xs.length - 1;
        else if (e.key === "Escape") { clear(); return; }
        else return;
        e.preventDefault();
        show();
      });
      svg.addEventListener("mousemove", (e) => {
        const m = svg.getScreenCTM();
        if (!m || !xs.length) return;
        const x = (e.clientX - m.e) / m.a;
        i = xs.reduce((best, v, k) => (Math.abs(v - x) < Math.abs(xs[best] - x) ? k : best), 0);
        show();
      });
      svg.addEventListener("mouseleave", () => { if (document.activeElement !== svg) clear(); });
      return;
    }

    pts.forEach((pt) => {
      const show = () => {
        tip.textContent = pt.getAttribute("aria-label");
        const dot = pt.querySelector(".viz-dot");
        place([dot], dot.getAttribute("cx"));
      };
      pt.addEventListener("mouseenter", show);
      pt.addEventListener("focus", show);
      pt.addEventListener("mouseleave", hide);
      pt.addEventListener("blur", hide);
      pt.addEventListener("keydown", (e) => { if (e.key === "Escape") { hide(); pt.blur(); } });
    });
  });
});
