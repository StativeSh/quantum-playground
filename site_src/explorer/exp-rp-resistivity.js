import {practical} from "./practical.js";

practical({
  id: "rp-resistivity",
  question: "How can you separate lead resistance from the resistance of the wire?",
  steps: ["Predict the shape before recording any points.", "Include short and long wires. Compare the slope and intercept of R against length."],
  control: ["Wire length", 0.1, 2, 0.05, 0.5, "m"],
  reading: "Resistance (Ω)", xLabel: "length (m)", yLabel: "resistance (Ω)",
  observe: (length,noise) => 0.15+1.1e-6*length/5e-7+0.035*noise,
  point: (length,r) => [length,r],
  constants: [
    {key: "rho", label: "Wire resistivity", unit: "Ω m", estimate: f => [5e-7*f.gradient,5e-7*f.gradientSE]},
  ],
});
