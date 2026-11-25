import {$, experiment, plot, tok} from "./core.js";

const lab=experiment("integrator-drift","Which methods keep the oscillator’s energy error bounded as you take more steps?",[
  "Keep the time step fixed and increase the number of steps. Compare the three final energy errors.",
  "Halve the time step and double the step count to compare methods at the same physical time.",
]);
const step=lab.range("dt","Time step",0.02,0.4,0.02,0.1,"s");
const steps=lab.range("steps","Steps",10,300,10,100);
const omega=lab.range("omega","Angular frequency",0.5,3,0.25,1,"rad/s");
const names=["Euler","RK4","Verlet"];
const results=names.map(name=>lab.result(name.toLowerCase(),name+" final relative energy error"));
const elapsed=lab.result("time","Simulated time","s",2);
function update() {
  const h=step(), n=steps(), k=omega()**2;
  const stepEuler=([x,v])=>[x+h*v,v-h*k*x];
  function stepRK4([x,v]) {
    const a1=-k*x, v2=v+h*a1/2, a2=-k*(x+h*v/2);
    const v3=v+h*a2/2, a3=-k*(x+h*v2/2), v4=v+h*a3, a4=-k*(x+h*v3);
    return [x+h*(v+2*v2+2*v3+v4)/6,v+h*(a1+2*a2+2*a3+a4)/6];
  }
  function stepVerlet([x,v]) {
    const next=x+h*v-0.5*h*h*k*x;
    return [next,v-0.5*h*k*(x+next)];
  }
  const colors=[tok("--accent-2"),tok("--accent"),tok("--fg")];
  const series=[stepEuler,stepRK4,stepVerlet].map((advance,m)=>{
    let state=[1,0], drift=0;
    const points=[[0,-16]];
    for(let i=1;i<=n;i++) {
      state=advance(state);
      drift=state[0]**2+state[1]**2/k-1;
      points.push([i*h,Math.log10(Math.max(1e-16,Math.abs(drift)))]);
    }
    results[m](drift.toExponential(5));
    return {points,color:colors[m],dash:m===1 ? [4,2] : []};
  });
  elapsed(n*h);
  plot($("integrator-drift-plot"),{xLabel:"time (s)",yLabel:"log₁₀ |relative energy error|",series});
}
lab.start(update);
