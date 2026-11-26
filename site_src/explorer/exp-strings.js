import {$, experiment, plot} from "./core.js";

const lab = experiment("strings", "Double the tension: what happens to the fundamental?", [
  "Tune the drive until the string forms one loop. Record the frequency.",
  "Double the tension at fixed length and mass per metre. Find the new one-loop frequency.",
]);
const tension = lab.range("tension", "Tension", 1, 100, 1, 16, "N");
const length = lab.range("length", "String length", 0.5, 2, 0.1, 1, "m");
const density = lab.range("density", "Mass per metre", 1, 20, 1, 10, "g/m");
const drive = lab.range("drive", "Driving frequency", 1, 300, 0.1, 20, "Hz");
const fundamental = lab.result("fundamental", "Fundamental frequency", "Hz", 3);
const mode = lab.result("mode", "Resonant harmonic", "", 0);
const nodes = lab.result("nodes", "Number of nodes", "", 0);
function update() {
  const f = Math.sqrt(tension() / (density()/1000)) / (2*length());
  const n = Math.max(1, Math.round(drive()/f));
  const resonant = Math.abs(n*f - drive()) <= 0.5;
  fundamental(f);
  mode(resonant ? n : "Between modes");
  nodes(resonant ? n+1 : "—");
  const points = Array.from({length: 500}, (_, i) => {
    const fraction = i/499;
    return [fraction*length(), resonant ? Math.sin(n*Math.PI*fraction) : 0];
  });
  plot($("strings-plot"), {xLabel: "position (m)", yLabel: "relative displacement", series: [{points}]});
}
lab.start(update);
