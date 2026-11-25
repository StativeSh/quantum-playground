import {$, experiment, prep, registerSim, tok, line, dot} from "./core.js";

const lab = experiment("lightclock", "At what speed does a moving clock run at half rate?", [
  "Raise the speed until a 1 µs tick takes about 2 µs in the lab.",
  "Compare the diagonal light path with the distance between the mirrors.",
]);
const beta = lab.range("beta", "Speed as a fraction of c", 0, 0.999, 0.001, 0.8);
const factor = lab.result("gamma", "Lorentz factor", "", 4);
const dilated = lab.result("time", "Lab duration of one tick", "µs", 4);
const surviving = lab.result("fraction", "Fraction reaching ground", "", 6);
let labTime = 0, gamma;
function draw() {
  const {ctx,w,h} = prep($("lightclock-plot"));
  const length = Math.min(h*0.6, w/(2*gamma+1));
  const phase = labTime/gamma % 2;
  const x0 = (w-2*beta()*gamma*length)/2;
  const x = x0 + phase*beta()*gamma*length;
  const y0 = (h+length)/2, y = y0 - (1-Math.abs(1-phase))*length;
  const trail = [[x0,y0]];
  if (phase>=1) trail.push([x0+beta()*gamma*length,y0-length]);
  line(ctx,[...trail,[x,y]],tok("--accent-2"));
  for (const mirror of [y0,y0-length]) line(ctx,[[x-12,mirror],[x+12,mirror]],tok("--fg"),3);
  dot(ctx,x,y,5,tok("--accent"));
}
function update() {
  gamma = 1/Math.sqrt(1-beta()**2);
  labTime = 0;
  factor(gamma);
  dilated(gamma);
  surviving(beta() === 0 ? 0 : Math.exp(-10000/(beta()*299792458*gamma*2.197e-6)));
}
lab.start(update,draw);
draw();
registerSim("lightclock","lightclock-play",dt => { labTime += dt; },draw);
