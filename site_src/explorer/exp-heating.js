import {$, experiment, plot} from "./core.js";

const lab = experiment("heating", "While the ice melts, where does the heater’s energy go?", [
  "Choose ice. Move the measurement point across the flat part of the curve and compare temperature and energy supplied.",
  "Double the power at the same mass. Compare the duration of melting and the energy needed for melting.",
]);
const power = lab.range("power", "Heater power", 100, 1000, 50, 500, "W");
const mass = lab.range("mass", "Sample mass", 0.1, 2, 0.1, 0.5, "kg");
const start = lab.range("start", "Starting temperature", 240, 273, 1, 263, "K");
const probe = lab.range("probe", "Measurement point along time axis", 0, 100, 1, 50, "%");
const duration = lab.result("duration", "Time spent melting", "s");
const time = lab.result("time", "Elapsed time", "s", 3);
const temperature = lab.result("temperature", "Sample temperature", "K");
const heat = lab.result("heat", "Energy supplied", "kJ", 3);

const materials = {
  water: {melting: 273.15, solid: 2100, latent: 334000, liquid: 4200},
  gallium: {melting: 302.91, solid: 371, latent: 80100, liquid: 397},
};
function update() {
  const {melting, solid, latent, liquid} = materials[$("heating-material").value];
  const rate = power() / mass(); // joules per kilogram per second
  const onset = solid * (melting - start()) / rate;
  const end = onset + latent / rate;
  const stop = end + 20 * liquid / rate;
  const t = stop * probe() / 100;
  const temp = start() + Math.min(t, onset) * rate / solid + Math.max(t - end, 0) * rate / liquid;
  time(t);
  temperature(temp);
  heat(power() * t / 1000);
  duration(latent / rate);
  plot($("heating-plot"), {xLabel: "time (s)", yLabel: "temperature (K)", series: [
    {points: [[0, start()], [onset, melting], [end, melting], [stop, melting + 20]]},
    {points: [[t, temp]]},
  ]});
}
lab.start(update);
