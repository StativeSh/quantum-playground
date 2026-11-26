import {practical} from "./practical.js";

practical({
  id: "rp-boyle",
  question: "What should pressure plotted against inverse volume look like for a sealed isothermal gas?",
  steps: ["Predict the shape before recording any points.", "Record several volumes. Fit through the origin and interpret the slope as pV."],
  control: ["Gas volume", 20, 100, 2, 50, "cm³"],
  reading: "Absolute pressure (kPa)", xLabel: "1/V (cm⁻³)", yLabel: "pressure (kPa)",
  observe: (volume,noise) => 5000/volume*(1+0.02*noise),
  point: (volume,p) => [1/volume,p],
  constants: [
    {key: "pv", label: "Pressure–volume product", unit: "Pa m³", estimate: f => [0.001*f.gradient,0.001*f.gradientSE]},
  ],
  throughOrigin: true,
});
