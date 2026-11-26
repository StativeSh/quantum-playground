import { $, tok, fmt, prep, axes, line, dot, onRedraw, registerSim } from "./core.js";

// ---------- Ising model (checkerboard Metropolis, J = 1) ----------
const N = 96, TC = 2 / Math.log(1 + Math.SQRT2);
const spins = new Int8Array(N * N);
const left = Array.from({length: N}, (_, x) => (x + N - 1) % N);
const right = Array.from({length: N}, (_, x) => (x + 1) % N);
const ising = { T: 2, mags: [], img: null };
const onsager = (T) => (T >= TC ? 0 : Math.pow(1 - Math.pow(Math.sinh(2 / T), -4), 1 / 8));
function isingFill(hot) { for (let i = 0; i < N * N; i++) spins[i] = hot ? (Math.random() < 0.5 ? 1 : -1) : 1; ising.mags = []; }
function sweep() {
  const T = ising.T, boltz = [Math.exp(-4 / T), Math.exp(-8 / T)];
  for (let colour = 0; colour < 2; colour++) {
    for (let y = 0; y < N; y++) {
      const up = ((y + N - 1) % N) * N, dn = ((y + 1) % N) * N, row = y * N;
      for (let x = (y + colour) % 2; x < N; x += 2) {
        const s = spins[row + x];
        const nb = spins[row + right[x]] + spins[row + left[x]] + spins[up + x] + spins[dn + x];
        const dE = 2 * s * nb;                                 // 0, 4 or 8 when it would cost energy
        if (dE <= 0 || Math.random() < boltz[dE / 4 - 1]) spins[row + x] = -s;
      }
    }
  }
  let m = 0; for (let i = 0; i < N * N; i++) m += spins[i];
  ising.mags.push(Math.abs(m) / (N * N));
  if (ising.mags.length > 300) ising.mags.shift();
}
function isingParams() {
  ising.T = +$("ising-T").value;
  ising.mags = [];
  $("ising-T-out").textContent = ising.T.toFixed(2);
  $("ising-ratio").textContent = fmt(ising.T / TC);
  $("ising-exact").textContent = fmt(onsager(ising.T));
  drawIsingCurve();
}
function stepIsing() { sweep(); sweep(); }
function drawIsing() {
  const cv = $("ising-lattice");
  if (cv.width !== N) { cv.width = N; cv.height = N; }
  const ctx = cv.getContext("2d");
  if (!ising.img) ising.img = ctx.createImageData(N, N);
  const up = tok("--fg"), d = ising.img.data;
  const hex = (c) => { const v = c.startsWith("#") ? c.slice(1) : "000000"; return [0, 2, 4].map((i) => parseInt(v.slice(i, i + 2), 16)); };
  const [r1, g1, b1] = hex(up), [r0, g0, b0] = hex(tok("--panel"));
  for (let i = 0; i < N * N; i++) {
    const on = spins[i] > 0;
    d[4 * i] = on ? r1 : r0; d[4 * i + 1] = on ? g1 : g0; d[4 * i + 2] = on ? b1 : b0; d[4 * i + 3] = 255;
  }
  ctx.putImageData(ising.img, 0, 0);
  if (ising.mags.length) {
    const avg = ising.mags.slice(-200).reduce((a, b) => a + b, 0) / Math.min(200, ising.mags.length);
    $("ising-m").textContent = fmt(avg);
    if (ising.mags.length % 10 === 0) drawIsingCurve(avg);
  } else $("ising-m").textContent = "–";
}
function drawIsingCurve(avg) {
  const { ctx, w, h } = prep($("ising-curve"));
  const { X, Y } = axes(ctx, w, h, [1, 4], [0, 1.05], { xlabel: "temperature T", ylabel: "|m|", nx: 6, ny: 4, l: 36 });
  const pts = [];
  for (let i = 0; i <= 300; i++) { const T = 1 + 3 * i / 300; pts.push([X(T), Y(onsager(T))]); }
  line(ctx, pts, tok("--accent"), 2);
  line(ctx, [[X(TC), Y(0)], [X(TC), Y(1.05)]], tok("--muted"), 1, [2, 4]);
  ctx.fillStyle = tok("--muted"); ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText("T_c", X(TC) + 4, Y(1.0));
  if (avg !== undefined) dot(ctx, X(ising.T), Y(avg), 6, tok("--accent-2"));
}
$("ising-T").addEventListener("input", isingParams);
$("ising-hot").addEventListener("click", () => { isingFill(true); drawIsing(); });
$("ising-cold").addEventListener("click", () => { isingFill(false); drawIsing(); });
isingFill(false);                                           // ordered start: no stuck stripe domains

isingParams();
drawIsing();
registerSim("ising", "ising-play", stepIsing, drawIsing);
onRedraw(() => { drawIsing(); drawIsingCurve(); });
