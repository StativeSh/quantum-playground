import { $, tok, fmt, prep, axes, line, dot, onRedraw, registerSim } from "./core.js";

// ---------- Lorenz attractor ----------
const lor = { a: [1, 1, 1], b: [1 + 1e-8, 1, 1], t: 0, ta: [], tb: [], seps: [] };
function lorRHS(s, p) { return [p.sigma * (s[1] - s[0]), s[0] * (p.rho - s[2]) - s[1], s[0] * s[1] - p.beta * s[2]]; }
function rk4(s, p, h) {
  const k1 = lorRHS(s, p), k2 = lorRHS(s.map((v, i) => v + h / 2 * k1[i]), p),
    k3 = lorRHS(s.map((v, i) => v + h / 2 * k2[i]), p), k4 = lorRHS(s.map((v, i) => v + h * k3[i]), p);
  return s.map((v, i) => v + h / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
}
function lorParams() {
  const p = { rho: +$("lor-rho").value, sigma: +$("lor-sigma").value, beta: +$("lor-beta").value };
  let start = [1, 1, 1];                                     // run onto the attractor first
  for (let i = 0; i < 5000; i++) start = rk4(start, p, 0.004);
  Object.assign(lor, { p, a: start, b: [start[0] + 1e-8, start[1], start[2]], t: 0, ta: [], tb: [], seps: [], separation: 1e-8 });
  $("lor-rho-out").textContent = p.rho.toFixed(1);
  $("lor-sigma-out").textContent = p.sigma.toFixed(1);
  $("lor-beta-out").textContent = p.beta.toFixed(2);
  const den = p.sigma - p.beta - 1, rhoH = den > 0 ? p.sigma * (p.sigma + p.beta + 3) / den : Infinity;
  $("lor-rhoH").textContent = Number.isFinite(rhoH) ? fmt(rhoH, 2) : "never";
  const chaotic = p.rho > rhoH, badge = $("lor-regime");
  badge.textContent = p.rho < 1 ? "ρ < 1 · decays to rest" : chaotic ? "ρ > ρ_H · chaotic" : "ρ < ρ_H · settles on a fixed point";
  badge.style.color = chaotic ? tok("--accent-2") : tok("--accent");
  $("lor-t").textContent = "0.0"; $("lor-sep").textContent = "1e-8";
  drawLorCurve();
}
function stepLor(dt) {
  const h = 0.004, n = Math.max(1, Math.round(dt / 0.016 * 4));
  for (let i = 0; i < n; i++) {
    lor.a = rk4(lor.a, lor.p, h); lor.b = rk4(lor.b, lor.p, h); lor.t += h;
    lor.ta.push([lor.a[0], lor.a[2]]); lor.tb.push([lor.b[0], lor.b[2]]);
  }
  if (lor.ta.length > 1500) { lor.ta.splice(0, lor.ta.length - 1500); lor.tb.splice(0, lor.tb.length - 1500); }
  const sep = Math.hypot(lor.a[0] - lor.b[0], lor.a[1] - lor.b[1], lor.a[2] - lor.b[2]);
  if (lor.t < 40) lor.seps.push([lor.t, Math.log10(Math.max(sep, 1e-16))]);
  lor.separation = sep;
}
function drawLor() {
  $("lor-t").textContent = lor.t.toFixed(1);
  $("lor-sep").textContent = (lor.separation ?? 1e-8).toExponential(1);
  drawLorCurve();
  const { ctx, w, h } = prep($("lor-anim"));
  const zmax = Math.max(50, lor.p.rho * 1.8), xm = Math.max(25, Math.sqrt(lor.p.beta * Math.max(lor.p.rho - 1, 1)) * 2.4);
  const X = (x) => w / 2 + x / xm * (w / 2 - 8), Y = (z) => h - 8 - z / zmax * (h - 16);
  line(ctx, lor.ta.map(([x, z]) => [X(x), Y(z)]), tok("--accent"), 2.6);    // wider, so it shows under B until they part
  line(ctx, lor.tb.map(([x, z]) => [X(x), Y(z)]), tok("--accent-2"), 1);
  dot(ctx, X(lor.a[0]), Y(lor.a[2]), 4, tok("--accent"));
  dot(ctx, X(lor.b[0]), Y(lor.b[2]), 4, tok("--accent-2"));
  ctx.fillStyle = tok("--muted"); ctx.font = `12px ${tok("--font-mono")}`; ctx.textAlign = "left"; ctx.textBaseline = "top";
  ctx.fillText("x → , z ↑", 8, 8);
}
function drawLorCurve() {
  const { ctx, w, h } = prep($("lor-curve"));
  const { X, Y } = axes(ctx, w, h, [0, 40], [-9, 2], { xlabel: "time", ylabel: "log₁₀ separation", nx: 4, ny: 5, l: 36 });
  line(ctx, [[X(0), Y(-8)], [X(40), Y(-8 + 0.906 * 40 / Math.LN10)]].map(([x, y]) => [x, Math.max(y, Y(2))]), tok("--muted"), 1, [4, 4]);
  line(ctx, lor.seps.map(([t, s]) => [X(t), Y(s)]), tok("--accent"), 1.5);
}
["lor-rho", "lor-sigma", "lor-beta"].forEach((id) => $(id).addEventListener("input", lorParams));

lorParams();
drawLor();
registerSim("lor", "lor-play", stepLor, drawLor);
onRedraw(drawLor);
