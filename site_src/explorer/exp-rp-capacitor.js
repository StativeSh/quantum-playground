import {practical} from "./practical.js";

practical({
  id: "rp-capacitor",
  question: "Which graph turns an exponential discharge into a straight line?",
  steps: ["Predict the shape before recording any points.", "Fit the natural logarithm of the measured voltage against time. Use the known resistance to find C."],
  control: ["Elapsed time", 0, 4, 0.1, 1, "s"],
  reading: "Voltage (V)", xLabel: "time (s)", yLabel: "ln(V / 1 V)",
  observe: (t,noise) => 5*Math.exp(-t/(10000*220e-6))*(1+0.02*noise),
  point: (t,v) => [t,Math.log(v)],
  constants: [
    {key: "c", label: "Capacitance", unit: "µF", estimate: f => [-1e6/(10000*f.gradient),1e6*f.gradientSE/(10000*f.gradient**2)]},
  ],
});
