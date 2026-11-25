import {$, experiment, plot} from "./core.js";

const lab = experiment("photoelectric", "Does brighter light give faster electrons or more electrons?", [
  "Choose sodium and set the frequency above its threshold. Set the retarding voltage to zero.",
  "Double the intensity. Compare maximum kinetic energy and current, then raise the retarding voltage until the current stops.",
]);
const frequency = lab.range("frequency", "Light frequency", 300, 1800, 10, 800, "THz");
const intensity = lab.range("intensity", "Incident intensity", 0, 10, 0.5, 2, "W/m²");
const voltage = lab.range("voltage", "Retarding voltage", 0, 6, 0.1, 0, "V");
const kinetic = lab.result("energy", "Maximum kinetic energy", "eV", 3);
const threshold = lab.result("threshold", "Threshold frequency", "THz");
const cutoff = lab.result("cutoff", "Stopping potential", "V", 3);
const current = lab.result("current", "Collected current", "µA", 3);

function update() {
  const h = 6.62607015e-34, charge = 1.602176634e-19;
  const photonEnergy = h * frequency() * 1e12;
  const work = Number($("photoelectric-metal").value);
  const energy = Math.max(0, photonEnergy / charge - work);
  const saturation = charge * intensity() * 1e-4 / photonEnergy * 1e6;
  const collected = v => energy > 0 ? saturation * Math.max(0, 1 - v / energy) : 0;
  kinetic(energy);
  threshold(work * charge / h / 1e12);
  cutoff(energy);
  current(collected(voltage()));
  plot($("photoelectric-plot"), {xLabel: "retarding voltage (V)", yLabel: "current (µA)",
    series: [{points: [[0, collected(0)], [energy, 0], [6, 0]]}, {points: [[voltage(), collected(voltage())]]}]});
}
lab.start(update);
