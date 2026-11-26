import {practical} from "./practical.js";

practical({
  id: "rp-spring",
  question: "Which feature of a period-squared graph tells you the spring stiffness?",
  steps: ["Predict the shape before recording any points.", "Double the mass and compare the periods. Fit T² against mass to estimate k."],
  control: ["Hanging mass", 0.05, 1, 0.025, 0.25, "kg"],
  reading: "Period (s)", xLabel: "mass (kg)", yLabel: "T² (s²)",
  observe: (m,noise) => 2*Math.PI*Math.sqrt(m/16)*(1+0.015*noise),
  point: (m,t) => [m,t*t],
  constants: [
    {key: "k", label: "Spring stiffness", unit: "N/m", estimate: f => [4*Math.PI**2/f.gradient,4*Math.PI**2*f.gradientSE/f.gradient**2]},
  ],
});
