import { $, tok, fmt, prep, axes, line, dot, onRedraw, registerSim } from "./core.js";

// ---------- Kepler orbits (GM = 1, start at r = 1) ----------
const orb = { x: 1, y: 0, vx: 0, vy: 1, t: 0, trail: [], lastCross: null, measured: null, points: [] };
function orbElements(f) {
  const v = f, energy = v * v / 2 - 1, h = v;                 // r0 = 1, velocity perpendicular
  const e = Math.sqrt(Math.max(0, 1 + 2 * energy * h * h));
  const a = energy < 0 ? -1 / (2 * energy) : Infinity;
  return { e, a, T: energy < 0 ? 2 * Math.PI * Math.pow(a, 1.5) : Infinity };
}
function orbParams() {
  const f = +$("orb-v").value, el = orbElements(f);
  Object.assign(orb, { x: 1, y: 0, vx: 0, vy: f, t: 0, trail: [], lastCross: null, measured: null, f, el });
  $("orb-v-out").textContent = f.toFixed(2);
  $("orb-e").textContent = fmt(el.e);
  $("orb-a").textContent = Number.isFinite(el.a) ? fmt(el.a) : "∞ (escapes)";
  $("orb-T").textContent = Number.isFinite(el.T) ? fmt(el.T, 2) : "–";
  $("orb-Tm").textContent = "waiting…";
  drawOrb(); drawOrbCurve();
}
function stepOrb(dt) {                                       // velocity Verlet, small fixed substeps
  const n = Math.max(1, Math.ceil(dt * 3 / 0.0005)), h = dt * 3 / n;   // 3 time units per second
  for (let i = 0; i < n; i++) {
    let r3 = Math.pow(orb.x * orb.x + orb.y * orb.y, 1.5);
    orb.vx -= 0.5 * h * orb.x / r3; orb.vy -= 0.5 * h * orb.y / r3;
    const yOld = orb.y;
    orb.x += h * orb.vx; orb.y += h * orb.vy;
    r3 = Math.pow(orb.x * orb.x + orb.y * orb.y, 1.5);
    orb.vx -= 0.5 * h * orb.x / r3; orb.vy -= 0.5 * h * orb.y / r3;
    orb.t += h;
    if (yOld < 0 && orb.y >= 0 && orb.x > 0) {             // crossed the +x axis going up: one full orbit
      const tc = orb.t - h * orb.y / (orb.y - yOld);
      orb.measured = tc;
      if (orb.lastCross === null) {
        orb.points = orb.points.filter((p) => Math.abs(p[0] - orb.el.a) > 1e-6).concat([[orb.el.a, tc]]).slice(-12);
        $("orb-Tm").textContent = fmt(tc, 2);
        drawOrbCurve();
      }
      orb.lastCross = tc;
    }
  }
  orb.trail.push([orb.x, orb.y]);
  if (orb.trail.length > 600) orb.trail.shift();
}
function drawOrb() {
  const { ctx, w, h } = prep($("orb-anim"));
  const el = orb.el, span = Number.isFinite(el.a) ? Math.max(1.15, el.a * (1 + el.e) * 1.08) : 4;
  const cx = w / 2;
  const S = Math.min(w, h) / (2 * span), X = (x) => cx + (x - (Number.isFinite(el.a) ? 1 - el.a : 0)) * S, Y = (y) => h / 2 - y * S;
  if (Number.isFinite(el.a) && el.e < 1) {                  // predicted ellipse: perihelion or aphelion at (1, 0)
    const b = el.a * Math.sqrt(1 - el.e * el.e), c = 1 - el.a;   // centre at x = 1 - a
    const pts = [];
    for (let i = 0; i <= 200; i++) { const th = 2 * Math.PI * i / 200; pts.push([X(c + el.a * Math.cos(th)), Y(b * Math.sin(th))]); }
    line(ctx, pts, tok("--accent-2"), 1.2, [5, 4]);
  }
  line(ctx, orb.trail.map(([x, y]) => [X(x), Y(y)]), tok("--accent"), 2);
  dot(ctx, X(0), Y(0), 7, tok("--accent-2"));
  if (Math.hypot(orb.x, orb.y) < 3 * span) dot(ctx, X(orb.x), Y(orb.y), 6, tok("--accent"));
  ctx.fillStyle = tok("--muted"); ctx.font = `12px ${tok("--font-mono")}`; ctx.textAlign = "left"; ctx.textBaseline = "top";
  ctx.fillText(`t = ${orb.t.toFixed(1)}`, 8, 8);
}
function drawOrbCurve() {
  const { ctx, w, h } = prep($("orb-curve"));
  const { X, Y } = axes(ctx, w, h, [0, 8], [0, 140], { xlabel: "semi-major axis a", ylabel: "period T", nx: 4, ny: 4, l: 40 });
  const pts = [];
  for (let i = 1; i <= 200; i++) { const a = 8 * i / 200; pts.push([X(a), Y(2 * Math.PI * Math.pow(a, 1.5))]); }
  line(ctx, pts, tok("--accent"), 2);
  orb.points.forEach(([a, T]) => dot(ctx, X(a), Y(T), 5, tok("--accent-2")));
}
$("orb-v").addEventListener("input", orbParams);

orbParams();
registerSim("orb", "orb-play", stepOrb, drawOrb);
onRedraw(() => { drawOrb(); drawOrbCurve(); });
