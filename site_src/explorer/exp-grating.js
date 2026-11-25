import { $, tok, fmt, prep, line, onRedraw } from "./core.js";

function drawGrating() {
  const density = Number($("grating-density").value);
  const ratio = density / 2000; // wavelength divided by grating period
  const limit = Math.floor(2000 / density);
  $("grating-density-out").textContent = density + " lines/mm";
  $("grating-angle").textContent = fmt(Math.asin(ratio) * 180 / Math.PI, 2) + "°";
  $("grating-count").textContent = 2 * limit + 1;
  const {ctx, w, h} = prep($("grating-plot"));
  const radius = Math.min(w/2 - 10, h - 34);
  const origin = [w/2, h-12];
  for (let m = -limit; m <= limit; m++) {
    const angle = Math.asin(Math.max(-1, Math.min(1, m * ratio)));
    line(ctx, [origin, [origin[0]+radius*Math.sin(angle), origin[1]-radius*Math.cos(angle)]], tok("--accent"), 2);
  }
}
$("grating-density").addEventListener("input", drawGrating);

drawGrating();
onRedraw(drawGrating);
