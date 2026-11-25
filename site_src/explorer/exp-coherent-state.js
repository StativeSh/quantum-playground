import {$, experiment, plot, registerSim} from "./core.js";

const lab=experiment("coherent-state","As a coherent packet crosses the well, does its width change?",[
  "Set a nonzero initial real amplitude. Compare the centre and width at the turning point and as the packet passes the origin.",
  "Add an imaginary amplitude and compare the mean momentum and probability density at your probe.",
]);
const real=lab.range("real","Initial Re α",-2,2,0.1,1);
const imag=lab.range("imag","Initial Im α",-2,2,0.1,0);
const frequency=lab.range("omega","Oscillator frequency",0.5,3,0.1,1);
const start=lab.range("time","Start time",0,10,0.1,0);
const probe=lab.range("probe","Probe position",-5,5,0.1,0);
const center=lab.result("center","Mean position","",6);
const momentum=lab.result("momentum","Mean momentum","",6);
const width=lab.result("width","Position standard deviation","",6);
const local=lab.result("density","Density at probe","",7);
let t=0, w=1, ar=1, ai=0;
function draw() {
  const re=ar*Math.cos(w*t)+ai*Math.sin(w*t), im=ai*Math.cos(w*t)-ar*Math.sin(w*t);
  const x0=Math.sqrt(2/w)*re;
  const density=x=>Math.sqrt(w/Math.PI)*Math.exp(-w*(x-x0)**2);
  center(x0); momentum(Math.sqrt(2*w)*im); width(1/Math.sqrt(2*w)); local(density(probe()));
  const points=Array.from({length:121},(_,i)=>[-8+i*16/120,density(-8+i*16/120)]);
  plot($("coherent-state-plot"),{xLabel:"position x",yLabel:"probability density",series:[{points},{points:[[probe(),density(probe())]]}]});
}
function drawWell() {
  const points=Array.from({length:81},(_,i)=>{const x=(i-40)/5;return [x,0.5*(w*x)**2];});
  const energy=w*(ar*ar+ai*ai+0.5);
  plot($("coherent-state-plot2"),{xLabel:"position x",yLabel:"potential and mean energy",series:[
    {points},{points:[[-8,energy],[8,energy]],dash:[4,4]},
  ]});
}
function reset() { w=frequency(); ar=real(); ai=imag(); t=start(); drawWell(); draw(); }
lab.start(reset,()=>{drawWell();draw();});
registerSim("coherent-state","coherent-state-play",dt=>{t+=dt;},draw);
