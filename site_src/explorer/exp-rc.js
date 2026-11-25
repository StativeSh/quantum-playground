import {$, experiment, plot} from "./core.js";

const lab = experiment("rc", "Double R: does charging take twice as long? Is the stored energy the same?", [
  "Choose charge. Read the time constant and the energy at full charge.",
  "Double the resistance without changing the capacitor or supply. Compare both readings, then try discharge.",
]);
const resistance = lab.range("resistance", "Resistance", 1, 20, 1, 5, "kΩ");
const capacitance = lab.range("capacitance", "Capacitance", 10, 200, 10, 100, "µF");
const supply = lab.range("supply", "Supply voltage", 1, 12, 1, 6, "V");
const time = lab.range("time", "Measurement time", 0, 5, 0.05, 0.5, "s");
const tau = lab.result("tau", "Time constant (63.2% of the change)", "s", 3);
const vc = lab.result("voltage", "Capacitor voltage", "V", 3);
const amps = lab.result("current", "Current into capacitor", "mA", 3);
const energy = lab.result("energy", "Energy at full charge", "mJ", 3);

function update() {
  const r = resistance() * 1000, c = capacitance() * 1e-6, v = supply();
  const charging = $("rc-mode").value === "charge";
  const voltage = t => v * (charging ? -Math.expm1(-t / (r*c)) : Math.exp(-t / (r*c)));
  const current = t => (charging ? 1 : -1) * 1000 * v / r * Math.exp(-t / (r*c));
  tau(r*c);
  vc(voltage(time()));
  amps(current(time()));
  energy(500 * c * v**2);
  function curve(canvas, label, fn) {
    // Resolve the transient even when the probe is many time constants later.
    const points = Array.from({length: 121}, (_, i) => {
      const t = 5 * r*c * i / 120;
      return [t, fn(t)];
    });
    if (time() > 5*r*c) points.push([time(), fn(time())]);
    plot($(canvas), {xLabel: "time (s)", yLabel: label, series: [{points}, {points: [[time(), fn(time())]]}]});
  }
  curve("rc-plot", "voltage (V)", voltage);
  curve("rc-plot2", "current (mA)", current);
}
lab.start(update);
