export const $ = (id) => document.getElementById(id);
export const tok = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
export const fmt = (x, d = 3) => Number.isFinite(x) ? x.toFixed(d) : "–";

// ---------- canvas + axes helpers ----------
export function prep(cv) {
  const dpr = window.devicePixelRatio || 1;
  const r = cv.getBoundingClientRect();
  const w = Math.max(1, r.width), h = Math.max(1, r.height);
  cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  return { ctx, w, h };
}
function niceStep(span, n) {
  const raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const f = raw / mag;
  return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag;
}
function ticks(min, max, n) {
  const s = niceStep(max - min, n), out = [];
  for (let v = Math.ceil(min / s - 1e-9) * s; v <= max + 1e-9; v += s) out.push(Math.abs(v) < s * 1e-9 ? 0 : v);
  return out;
}
// Draws a frame with ticks; returns scale functions. pad = room for labels.
export function axes(ctx, w, h, xr, yr, opt = {}) {
  const pad = { l: opt.l ?? 46, r: opt.r ?? 12, t: opt.t ?? 10, b: opt.b ?? 34 };
  const X = (x) => pad.l + (x - xr[0]) / (xr[1] - xr[0]) * (w - pad.l - pad.r);
  const Y = (y) => h - pad.b - (y - yr[0]) / (yr[1] - yr[0]) * (h - pad.t - pad.b);
  ctx.font = `12px ${tok("--font-mono")}`;
  ctx.lineWidth = 1;
  ctx.strokeStyle = tok("--grid"); ctx.fillStyle = tok("--muted");
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  for (const v of ticks(xr[0], xr[1], opt.nx ?? 6)) {
    ctx.beginPath(); ctx.moveTo(X(v), pad.t); ctx.lineTo(X(v), h - pad.b); ctx.stroke();
    ctx.fillText(opt.xfmt ? opt.xfmt(v) : +v.toPrecision(4) + "", X(v), h - pad.b + 5);
  }
  ctx.textAlign = "right"; ctx.textBaseline = "middle";
  for (const v of ticks(yr[0], yr[1], opt.ny ?? 4)) {
    ctx.beginPath(); ctx.moveTo(pad.l, Y(v)); ctx.lineTo(w - pad.r, Y(v)); ctx.stroke();
    ctx.fillText(+v.toPrecision(4) + "", pad.l - 6, Y(v));
  }
  ctx.fillStyle = tok("--fg");
  if (opt.xlabel) { ctx.textAlign = "right"; ctx.textBaseline = "bottom"; ctx.fillText(opt.xlabel, w - pad.r, h - 2); }
  if (opt.ylabel) { ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText(opt.ylabel, pad.l + 4, pad.t + 2); }
  return { X, Y, pad };
}
export function line(ctx, pts, color, width = 2, dash = []) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.lineJoin = "round";
  ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke(); ctx.restore();
}
export function dot(ctx, x, y, r, color) { ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.fill(); }

const redraws = new Set();
let redrawFrame;
export function onRedraw(draw) {
  redraws.add(draw);
}
function scheduleRedraw() {
  if (redrawFrame) return;
  redrawFrame = requestAnimationFrame(() => {
    redrawFrame = null;
    for (const draw of redraws) draw();
  });
}
new ResizeObserver(scheduleRedraw).observe(document.querySelector(".wrap"));
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", scheduleRedraw);
new MutationObserver(scheduleRedraw).observe(document.documentElement, {
  attributes: true, attributeFilter: ["data-theme"],
});
document.fonts.ready.then(scheduleRedraw);

const simulations = new Map();
let frame;
function animate(now) {
  frame = null;
  for (const sim of simulations.values()) {
    if (!sim.playing || !sim.visible) continue;
    if (sim.last !== null) sim.step(Math.min(0.05, (now - sim.last) / 1000));
    sim.last = now;
    sim.draw();
    scheduleAnimation();
  }
}
function scheduleAnimation() {
  if (frame == null) frame = requestAnimationFrame(animate);
}
const visibility = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const sim = simulations.get(entry.target);
    sim.visible = entry.isIntersecting;
    sim.last = null;
    if (sim.visible && sim.playing) scheduleAnimation();
  }
});

export function registerSim(name, buttonId, step, draw) {
  const button = $(buttonId);
  const section = button.closest(".experiment");
  const sim = {step, draw, visible: false, playing: false, last: null};
  simulations.set(section, sim);
  visibility.observe(section);
  function setPlaying(on) {
    sim.playing = on;
    sim.last = null;
    button.textContent = on ? "Pause" : "Play";
    button.setAttribute("aria-pressed", String(on));
    if (on && sim.visible) scheduleAnimation();
  }
  button.addEventListener("click", () => setPlaying(!sim.playing));
  // Capture non-bubbling inputs too. Draw after the control has updated its state.
  let inputFrame = null;
  section.addEventListener("input", () => {
    if (inputFrame !== null || (sim.visible && sim.playing)) return;
    inputFrame = requestAnimationFrame(() => {
      inputFrame = null;
      if (!sim.visible || !sim.playing) draw();
    });
  }, true);
  setPlaying(!matchMedia("(prefers-reduced-motion: reduce)").matches);
  return setPlaying;
}

export function slider({id, label, min, max, step, value, unit = "", format = String}) {
  const element = document.createElement("div");
  element.className = "control";
  const caption = document.createElement("label");
  caption.htmlFor = id;
  const output = document.createElement("output");
  output.htmlFor.add(id);
  const input = document.createElement("input");
  Object.assign(input, {type: "range", id, min, max, step, value});
  const update = () => { output.value = [format(input.valueAsNumber), unit].filter(Boolean).join(" "); };
  input.addEventListener("input", update);
  update();
  caption.append(label, output);
  element.append(caption, input);
  return {element, input};
}

export function readout({id, label, format = String}) {
  const element = document.createElement("dl");
  element.className = "readouts";
  const term = document.createElement("dt");
  term.textContent = label;
  const value = document.createElement("dd");
  value.id = id;
  element.append(term, value);
  return {element, set: v => { value.textContent = format(v); }};
}

// Each series supplies {points: [[x, y], ...], color?, dash?} in data coordinates.
export function plot(canvas, {xLabel, yLabel, series}) {
  const {ctx, w, h} = prep(canvas);
  function range(axis) {
    let min = Infinity, max = -Infinity;
    for (const {points} of series) {
      for (const point of points) {
        min = Math.min(min, point[axis]);
        max = Math.max(max, point[axis]);
      }
    }
    if (min > max) return [0, 1];
    return min === max ? [min - 1, max + 1] : [min, max];
  }
  const {X, Y} = axes(ctx, w, h, range(0), range(1), {xlabel: xLabel, ylabel: yLabel});
  series.forEach(({points, color, dash}, i) => {
    const stroke = color ?? tok(i % 2 ? "--accent-2" : "--accent");
    if (points.length === 1) {
      const [[x, y]] = points;
      dot(ctx, X(x), Y(y), 4, stroke);
    } else {
      line(ctx, points.map(([x, y]) => [X(x), Y(y)]), stroke, 2, dash);
    }
  });
}

// Mulberry32, with an unsigned 32-bit state and samples in [0, 1).
export function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = Math.imul(state ^ state >>> 15, state | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

export function measureTable({columns}) {
  const element = document.createElement("table");
  const header = element.createTHead().insertRow();
  for (const column of columns) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = column;
    header.append(cell);
  }
  const body = element.createTBody();
  function addRow(values) {
    if (values.length !== columns.length) throw new RangeError("Expected one value per column");
    const row = body.insertRow();
    for (const value of values) row.insertCell().textContent = value;
  }
  return {element, addRow, clear: () => body.replaceChildren()};
}

// Ordinary least squares, with residual variance estimated using n - 2 degrees of freedom.
export function fitLine(xs, ys) {
  const n = xs.length;
  if (n < 2 || n !== ys.length || !xs.every(Number.isFinite) || !ys.every(Number.isFinite)) {
    throw new RangeError("Expected at least two finite (x, y) pairs");
  }
  const mean = values => values.reduce((a, b) => a + b, 0) / n;
  const xMean = mean(xs), yMean = mean(ys);
  const sxx = xs.reduce((sum, x) => sum + (x - xMean) ** 2, 0);
  if (sxx === 0) throw new RangeError("A line needs distinct x values");
  const gradient = xs.reduce((sum, x, i) => sum + (x - xMean) * (ys[i] - yMean), 0) / sxx;
  const intercept = yMean - gradient * xMean;
  const rss = ys.reduce((sum, y, i) => sum + ((y - yMean) - gradient * (xs[i] - xMean)) ** 2, 0);
  const variance = rss / (n - 2);
  return {gradient, intercept,
    gradientSE: n > 2 ? Math.sqrt(variance / sxx) : null,
    interceptSE: n > 2 ? Math.sqrt(variance * (1 / n + xMean ** 2 / sxx)) : null};
}

export function guided({question, steps}) {
  const element = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = question;
  const list = document.createElement("ol");
  for (const step of steps) {
    const item = document.createElement("li");
    item.textContent = step;
    list.append(item);
  }
  element.append(summary, list);
  return element;
}

// Mount the common controls beside an experiment's canvas.
export function experiment(id, question, steps) {
  const section = $(id);
  section.querySelector(".prediction").append(guided({question, steps}));
  function range(key, label, min, max, step, value, unit = "") {
    const control = slider({id: id + "-" + key, label, min, max, step, value, unit});
    section.querySelector(".controls").append(control.element);
    return () => control.input.valueAsNumber;
  }
  function result(key, label, unit = "", digits = 2) {
    const field = readout({id: id + "-" + key, label,
      format: value => typeof value === "number" ? [value.toFixed(digits), unit].filter(Boolean).join(" ") : value});
    section.querySelector(".results").append(field.element);
    return field.set;
  }
  function start(update, redraw = update) {
    for (const control of section.querySelectorAll("input, select")) control.addEventListener("input", update);
    update();
    onRedraw(redraw);
  }
  return {range, result, start};
}
