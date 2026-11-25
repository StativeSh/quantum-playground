import {practical} from "./practical.js";

practical({
  id: "rp-searchcoil",
  question: "How would you infer peak flux linkage from a graph against cos θ?",
  steps: ["Predict the shape before recording any points.", "Measure at several angles to the normal. Use the known angular frequency to convert the slope to flux linkage."],
  control: ["Angle to normal", 0, 180, 5, 45, "°"],
  reading: "Signed emf amplitude (V)", xLabel: "cos θ", yLabel: "signed peak emf (V)",
  observe: (angle,noise) => 2*Math.PI*50*0.012*Math.cos(angle*Math.PI/180)+0.06*noise,
  point: (angle,v) => [Math.cos(angle*Math.PI/180),v],
  constants: [
    {key: "flux", label: "Peak flux linkage", unit: "Wb turns", estimate: f => [f.gradient/(2*Math.PI*50),f.gradientSE/(2*Math.PI*50)]},
  ],
});
