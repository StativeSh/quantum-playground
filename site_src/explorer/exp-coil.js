import { $, tok, fmt, prep, axes, line, onRedraw } from "./core.js";

function drawCoil() {
  const angle = Number($("coil-angle").value);
  const emf = deg => 2 * Math.sin(deg * Math.PI / 180);
  $("coil-angle-out").textContent = angle + "°";
  $("coil-flux").textContent = fmt(0.2 * Math.cos(angle * Math.PI / 180)) + " Wb turns";
  $("coil-emf").textContent = fmt(emf(angle)) + " V";
  const {ctx, w, h} = prep($("coil-plot"));
  const {X, Y} = axes(ctx, w, h, [0, 360], [-2.2, 2.2], {xlabel: "angle (°)", ylabel: "emf (V)"});
  const curve = Array.from({length: 181}, (_, i) => [X(2*i), Y(emf(2*i))]);
  line(ctx, curve, tok("--accent"), 2);
  ctx.fillStyle = tok("--accent-2");
  ctx.beginPath(); ctx.arc(X(angle), Y(emf(angle)), 5, 0, 2*Math.PI); ctx.fill();
}
$("coil-angle").addEventListener("input", drawCoil);

drawCoil();
onRedraw(drawCoil);
