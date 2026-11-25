import { $, tok, fmt, prep, axes, line, dot, onRedraw } from "./core.js";

// ---------- tunnelling: exact stationary scattering state ----------
const C = (re, im = 0) => ({ re, im });
const add = (a, b) => C(a.re + b.re, a.im + b.im);
const sub = (a, b) => C(a.re - b.re, a.im - b.im);
const mul = (a, b) => C(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
const div = (a, b) => { const d = b.re * b.re + b.im * b.im; return C((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d); };
const scl = (a, s) => C(a.re * s, a.im * s);
const cexp = (a) => { const m = Math.exp(a.re); return C(m * Math.cos(a.im), m * Math.sin(a.im)); };
const abs2 = (a) => a.re * a.re + a.im * a.im;

// psi = e^{ikx} + r e^{-ikx} (x<0); A e^{qx} + B e^{-qx} (0<x<a); t e^{ikx} (x>a)
function scatter(E, V0, a) {
  if (Math.abs(E - V0) < 1e-7) E = V0 + 1e-7;
  const k = Math.sqrt(2 * E), d = 2 * (V0 - E);
  const q = d > 0 ? C(Math.sqrt(d)) : C(0, Math.sqrt(-d));
  const ik = C(0, k), ikq = div(ik, q), eika = cexp(C(0, k * a));
  let A = mul(mul(eika, scl(add(C(1), ikq), 0.5)), cexp(scl(q, -a)));   // with t = 1
  let B = mul(mul(eika, scl(sub(C(1), ikq), 0.5)), cexp(scl(q, a)));
  const s = scl(add(add(A, B), div(mul(q, sub(A, B)), ik)), 0.5);         // incident amplitude for t = 1
  const t = div(C(1), s), r = sub(div(add(A, B), s), C(1));
  A = div(A, s); B = div(B, s);
  return { k, q, a, A, B, t, r, T: abs2(t), R: abs2(r) };
}
function psiAt(x, S) {
  if (x < 0) return add(cexp(C(0, S.k * x)), mul(S.r, cexp(C(0, -S.k * x))));
  if (x <= S.a) return add(mul(S.A, cexp(scl(S.q, x))), mul(S.B, cexp(scl(S.q, -x))));
  return mul(S.t, cexp(C(0, S.k * x)));
}
function tunParams() {
  const E = +$("tun-E").value, V0 = +$("tun-V").value, a = +$("tun-a").value;
  $("tun-E-out").textContent = E.toFixed(2);
  $("tun-V-out").textContent = V0.toFixed(2);
  $("tun-a-out").textContent = a.toFixed(2);
  const S = scatter(E, V0, a);
  $("tun-T").textContent = S.T < 1e-3 ? S.T.toExponential(2) : fmt(S.T);
  $("tun-R").textContent = fmt(1 - S.T);
  $("tun-lam").textContent = `${fmt(2 * Math.PI / S.k, 2)}`;
  const below = E < V0;
  const badge = $("tun-regime");
  badge.textContent = below ? "E < V₀ · tunnelling" : "E > V₀ · over the barrier";
  badge.style.color = below ? tok("--accent") : tok("--accent-2");
  drawPsi(S, E, V0); drawTunCurve(E, V0, a);
}
function drawPsi(S, E, V0) {
  const { ctx, w, h } = prep($("tun-psi"));
  const xr = [-10, S.a + 10];
  const { X, Y } = axes(ctx, w, h, xr, [-2.2, 4.2], { xlabel: "x", nx: 8, ny: 4, l: 34 });
  ctx.fillStyle = tok("--barrier");
  ctx.fillRect(X(0), Y(4.2), X(S.a) - X(0), Y(-2.2) - Y(4.2));
  const re = [], dens = [];
  for (let i = 0; i <= 900; i++) {
    const x = xr[0] + (xr[1] - xr[0]) * i / 900, p = psiAt(x, S);
    re.push([X(x), Y(p.re)]); dens.push([X(x), Y(abs2(p))]);
  }
  line(ctx, re, tok("--accent-2"), 1.2, [4, 3]);
  line(ctx, dens, tok("--accent"), 2.2);
}
function drawTunCurve(E, V0, a) {
  const { ctx, w, h } = prep($("tun-curve"));
  const { X, Y } = axes(ctx, w, h, [0, 6], [0, 1.05], { xlabel: "energy E", ylabel: "transmission T", nx: 6, ny: 4, l: 40 });
  line(ctx, [[X(V0), Y(0)], [X(V0), Y(1.05)]], tok("--muted"), 1, [2, 4]);
  ctx.fillStyle = tok("--muted"); ctx.textAlign = "left"; ctx.textBaseline = "top";
  ctx.fillText("V₀", X(V0) + 4, Y(1.0));
  const pts = [];
  for (let i = 1; i <= 600; i++) { const e = 6 * i / 600; pts.push([X(e), Y(scatter(e, V0, a).T)]); }
  line(ctx, pts, tok("--accent"), 2);
  dot(ctx, X(E), Y(scatter(E, V0, a).T), 5, tok("--accent-2"));
}
["tun-E", "tun-V", "tun-a"].forEach((id) => $(id).addEventListener("input", tunParams));

tunParams();
onRedraw(tunParams);
