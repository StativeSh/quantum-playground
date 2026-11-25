import {$, experiment, prep, tok, plot} from "./core.js";

const lab = experiment("binding", "For A = 56, which Z is most tightly bound?", [
  "Fix the mass number at 56. Move the proton number across the peak and compare neighbouring nuclei.",
  "Inspect the contributions for odd and even proton numbers. Does the maximum lie at A/2?",
]);
const mass = lab.range("a","Mass number A",8,240,1,56);
const protons = lab.range("z","Proton number Z",1,55,1,26);
const binding = lab.result("energy","Binding per nucleon","MeV",4);
const release = lab.result("release","Reaction energy released","MeV",3);
function terms(a,z) {
  return [15.75*a, -17.8*a**(2/3), -0.711*z*(z-1)/Math.cbrt(a),
    -23.7*(a-2*z)**2/a, a%2 ? 0 : (z%2 ? -12 : 12)/Math.sqrt(a)];
}
const total = (a,z) => terms(a,z).reduce((sum,v) => sum+v,0);
function update() {
  const a = mass(), control = $("binding-z");
  if (+control.max !== a-1) {
    control.max = a-1;
    control.labels[0].querySelector("output").value = control.value;
  }
  const z = protons(), b = total(a,z);
  binding(b/a);
  if ($("binding-reaction").value === "fusion") release(total(2*a,2*z)-2*b);
  else {
    const leftA = Math.floor(a/2), leftZ = Math.floor(z/2);
    const valid = leftZ > 0 && leftZ < leftA && z-leftZ < a-leftA;
    release(valid ? total(leftA,leftZ)+total(a-leftA,z-leftZ)-b : "Choose a nucleus with two physical fragments");
  }
  const {ctx,w,h} = prep($("binding-plot"));
  const names = ["volume","surface","Coulomb","asymmetry","pairing"];
  const values = terms(a,z), scale = w*0.27/Math.max(...values.map(Math.abs));
  ctx.font = "12px system-ui";
  values.forEach((v,i) => {
    const y = (i+0.5)*h/5;
    ctx.fillStyle = tok(v>=0 ? "--accent" : "--accent-2");
    ctx.fillRect(w*0.68, y-5, v*scale,10);
    ctx.fillStyle = tok("--fg");
    ctx.fillText(names[i]+" "+v.toFixed(1)+" MeV",4,y+4);
  });
  const points = Array.from({length:a-1}, (_,i) => [i+1,total(a,i+1)/a]);
  plot($("binding-plot2"),{xLabel:"proton number Z",yLabel:"MeV per nucleon",series:[{points},{points:[[z,b/a]]}]});
}
lab.start(update);
