import {$, experiment, plot} from "./core.js";

const lab = experiment("spectrometer", "Two isotopes enter at the same speed: which lands further away?", [
  "Match the ion speed to the speed passed by the selector. Record the landing distance.",
  "Keep speed, charge and fields fixed. Change only the mass and compare the distances.",
]);
const electric = lab.range("electric", "Electric field", 1, 20, 1, 10, "kV/m");
const magnetic = lab.range("magnetic", "Magnetic field", 0.1, 1, 0.1, 0.5, "T");
const speed = lab.range("speed", "Ion speed", 1, 100, 1, 20, "km/s");
const mass = lab.range("mass", "Ion mass", 1, 100, 1, 20, "u");
const charge = lab.range("charge", "Ion charge", 1, 3, 1, 1, "e");
const selected = lab.result("selected", "Speed passed", "km/s", 3);
const radius = lab.result("radius", "Analyser radius at this speed", "mm", 3);
const landing = lab.result("landing", "Detector displacement", "mm", 3);
function update() {
  const v = speed()*1000, drift = electric()*1000/magnetic();
  const omega = charge()*1.602176634e-19*magnetic()/(mass()*1.66053906892e-27);
  const r = v/omega, width = drift/omega;
  const passed = Math.abs(v-drift) < 1e-6;
  selected(drift/1000);
  radius(1000*r);
  landing(passed ? -2000*r : "Blocked by selector");
  // Crossed-field cycloid: start along +x, B out of the page, E along +y.
  const points = [];
  for (let i = 0; i <= 640; i++) {
    const phase = i/100;
    const x = (drift*phase + (v-drift)*Math.sin(phase))/omega;
    const y = (v-drift)*(Math.cos(phase)-1)/omega;
    points.push([1000*(x-width), 1000*y]);
    if (x >= width) break;
  }
  if (passed) {
    for (let i = 0; i <= 100; i++) {
      const a = Math.PI*i/100;
      points.push([1000*r*Math.sin(a), 1000*r*(Math.cos(a)-1)]);
    }
  }
  plot($("spectrometer-plot"), {xLabel: "x from slit (mm)", yLabel: "y (mm)", series: [{points}]});
}
lab.start(update);
