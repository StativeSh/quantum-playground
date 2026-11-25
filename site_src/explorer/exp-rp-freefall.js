import {practical} from "./practical.js";

practical({
  id: "rp-freefall",
  question: "How could a graph of height against fall time squared give g?",
  steps: ["Predict the shape before recording any points.", "Compare several release heights. Which fitted coefficient contains the acceleration?"],
  control: ["Height", 0.1, 2, 0.05, 0.5, "m"],
  reading: "Fall time (s)", xLabel: "t² (s²)", yLabel: "height (m)",
  observe: (h,noise) => Math.sqrt(2*h/9.81)*(1+0.012*noise),
  point: (h,t) => [t*t,h],
  constants: [
    {key: "g", label: "Gravitational acceleration", unit: "m/s²", estimate: f => [2*f.gradient,2*f.gradientSE]},
  ],
});
