import {practical} from "./practical.js";

practical({
  id: "rp-melde",
  question: "How would a heavier string change the slope of f² against tension?",
  steps: ["Predict the shape before recording any points.", "Use the length and the fitted slope to infer mass per metre."],
  control: ["Tension", 2, 40, 1, 10, "N"],
  reading: "Frequency (Hz)", xLabel: "tension (N)", yLabel: "f² (Hz²)",
  observe: (tension,noise) => Math.sqrt(tension/0.002)/(2*0.8)*(1+0.012*noise),
  point: (t,f) => [t,f*f],
  constants: [
    {key: "mu", label: "Mass per unit length", unit: "kg/m", estimate: f => [1/(4*0.8**2*f.gradient),f.gradientSE/(4*0.8**2*f.gradient**2)]},
  ],
});
