import { $, tok, fmt, prep, axes, line, onRedraw } from "./core.js";

// ---------- double slit ----------
function wavelengthRGB(nm) {                // approximate visible-spectrum colour
  let r = 0, g2 = 0, b = 0;
  if (nm < 440) { r = -(nm - 440) / 60; b = 1; }
  else if (nm < 490) { g2 = (nm - 440) / 50; b = 1; }
  else if (nm < 510) { g2 = 1; b = -(nm - 510) / 20; }
  else if (nm < 580) { r = (nm - 510) / 70; g2 = 1; }
  else if (nm < 645) { r = 1; g2 = -(nm - 645) / 65; }
  else r = 1;
  const fall = nm < 420 ? 0.3 + 0.7 * (nm - 380) / 40 : nm > 680 ? 0.3 + 0.7 * (750 - nm) / 70 : 1;
  return [r, g2, b].map((c) => Math.round(255 * Math.pow(c * fall, 0.8)));
}
function slitState() {
  const lam = +$("slit-lam").value * 1e-9, d = +$("slit-d").value * 1e-3,
    w = Math.min(+$("slit-w").value * 1e-3, 0.9 * d), L = +$("slit-L").value;
  return { lam, d, w, L };
}
function intensity(ymm, s) {
  const y = ymm * 1e-3, sin = y / Math.hypot(y, s.L);
  const beta = Math.PI * s.w * sin / s.lam, alpha = Math.PI * s.d * sin / s.lam;
  const env = Math.abs(beta) < 1e-12 ? 1 : (Math.sin(beta) / beta) ** 2;
  return { I: Math.cos(alpha) ** 2 * env, env };
}
let markedFringes = 0;
let measuredSpacing = null;
let slitReference = null;

// Locate the first off-centre maximum of the displayed intensity profile.
function firstBrightFringe(s, ymax) {
  const step = ymax / 12000;
  let previous = 1, current = intensity(step, s).I;
  for (let i = 1; i < 12000; i++) {
    const next = intensity((i + 1) * step, s).I;
    if (current > previous && current >= next) return i * step;
    previous = current;
    current = next;
  }
  return null;
}
function slitScreenLimit(s) {
  return Math.min(80, 2.2 * s.lam * s.L / s.w * 1e3);
}
function slitParams() {
  const s = slitState();
  $("slit-lam-out").textContent = `${$("slit-lam").value} nm`;
  $("slit-d-out").textContent = `${(+$("slit-d").value).toFixed(2)} mm`;
  $("slit-w-out").textContent = `${(s.w * 1e3).toFixed(3)} mm`;
  $("slit-L-out").textContent = `${s.L.toFixed(2)} m`;
  const dy = s.lam * s.L / s.d * 1e3, env = s.lam * s.L / s.w * 1e3;
  $("slit-dy").textContent = `${fmt(dy, 2)} mm`;
  $("slit-env").textContent = `±${fmt(env, 1)} mm`;
  $("slit-n").textContent = `${2 * Math.floor(s.d / s.w - 1e-9) + 1}`;
  const ymax = slitScreenLimit(s);
  const spacing = measuredSpacing;
  $("slit-mark").disabled = markedFringes === 2;
  $("slit-mark").textContent = ["Mark central fringe", "Mark next bright fringe", "Both fringes marked"][markedFringes];
  $("slit-save").disabled = spacing === null;
  $("slit-save").textContent = slitReference ? "Replace reference" : "Save reference";
  $("slit-measured").textContent = spacing !== null ? `Measured spacing: ${fmt(spacing, 3)} mm` :
    markedFringes === 1 ? "Central fringe marked at 0 mm." : "";
  $("slit-comparison").textContent = "";
  if (spacing !== null && slitReference) {
    const predictedRatio = dy / slitReference.predicted;
    $("slit-comparison").textContent = `Current / reference: measured ${fmt(spacing / slitReference.spacing)} ×; small-angle prediction ${fmt(predictedRatio)} ×.`;
  }
  drawBand(s, ymax, spacing); drawSlitCurve(s, ymax);
}
function drawBand(s, ymax, spacing) {
  const cv = $("slit-band"), { ctx, w, h } = prep(cv);
  const [r, g2, b] = wavelengthRGB(s.lam * 1e9);
  ctx.fillStyle = tok("--screen"); ctx.fillRect(0, 0, w, h);
  const n = Math.ceil(w);
  for (let i = 0; i < n; i++) {
    const y = -ymax + 2 * ymax * (i + 0.5) / n;
    const v = Math.pow(intensity(y, s).I, 0.6);
    ctx.fillStyle = `rgba(${r},${g2},${b},${v})`;
    ctx.fillRect(i, 0, 1.2, h);
  }
  if (markedFringes) {
    ctx.fillStyle = "white";
    for (const y of spacing === null ? [0] : [0, spacing]) {
      const x = (1 + y / ymax) * w / 2;
      ctx.beginPath();
      ctx.moveTo(x, h - 10); ctx.lineTo(x - 4, h); ctx.lineTo(x + 4, h);
      ctx.fill();
    }
  }
}
function drawSlitCurve(s, ymax) {
  const { ctx, w, h } = prep($("slit-curve"));
  const { X, Y } = axes(ctx, w, h, [-ymax, ymax], [0, 1.05], { xlabel: "position on screen (mm)", nx: 8, ny: 4, l: 36 });
  const I = [], E = [], n = Math.max(1200, Math.ceil(w * 3));
  for (let i = 0; i <= n; i++) {
    const y = -ymax + 2 * ymax * i / n, v = intensity(y, s);
    I.push([X(y), Y(v.I)]); E.push([X(y), Y(v.env)]);
  }
  line(ctx, E, tok("--accent-2"), 1.2, [5, 4]);
  line(ctx, I, tok("--accent"), 1.6);
}
function markFringe() {
  markedFringes++;
  if (markedFringes === 2) {
    const s = slitState();
    measuredSpacing = firstBrightFringe(s, slitScreenLimit(s));
  }
  slitParams();
}
$("slit-mark").addEventListener("click", markFringe);
$("slit-band").addEventListener("click", (event) => {
  if (markedFringes === 2) return;
  const s = slitState(), limit = slitScreenLimit(s);
  const rect = event.currentTarget.getBoundingClientRect();
  const position = (2 * (event.clientX - rect.left) / rect.width - 1) * limit;
  const adjacent = firstBrightFringe(s, limit);
  const target = markedFringes === 0 ? 0 : adjacent;
  if (adjacent !== null && Math.abs(position - target) <= adjacent / 2) {
    markFringe();
  } else {
    $("slit-measured").textContent = markedFringes === 0 ?
      "Start at the bright fringe in the centre." : "Choose the first bright fringe to the right of centre.";
  }
});
$("slit-save").addEventListener("click", () => {
  const s = slitState();
  const spacing = measuredSpacing;
  slitReference = { spacing, predicted: s.lam * s.L / s.d * 1e3 };
  $("slit-reference").textContent = `Reference: ${fmt(spacing)} mm at d = ${fmt(s.d * 1e3, 2)} mm, λ = ${$("slit-lam").value} nm, L = ${fmt(s.L, 2)} m, w = ${fmt(s.w * 1e3)} mm.`;
  slitParams();
});
["slit-lam", "slit-d", "slit-w", "slit-L"].forEach((id) => $(id).addEventListener("input", () => {
  markedFringes = 0;
  measuredSpacing = null;
  slitParams();
}));

slitParams();
onRedraw(slitParams);
