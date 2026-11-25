import {practical} from "./practical.js";

practical({
  id: "rp-emf",
  question: "What do the intercept and gradient tell you about the cell?",
  steps: ["Predict the shape before recording any points.", "Record terminal voltages over a wide range of currents. Extrapolate to zero current."],
  control: ["Load current", 0.05, 1.5, 0.05, 0.5, "A"],
  reading: "Terminal voltage (V)", xLabel: "current (A)", yLabel: "terminal voltage (V)",
  observe: (i,noise) => 3.2-0.8*i+0.035*noise,
  point: (i,v) => [i,v],
  constants: [
    {key: "emf", label: "Cell emf", unit: "V", estimate: f => [f.intercept,f.interceptSE]},
    {key: "r", label: "Internal resistance", unit: "Ω", estimate: f => [-f.gradient,f.gradientSE]},
  ],
});
