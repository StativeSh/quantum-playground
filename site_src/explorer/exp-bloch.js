import {$, experiment, prep, tok, line, dot, registerSim} from "./core.js";

const lab=experiment("bloch","Which component of the spin stays fixed as it precesses about z?",[
  "Choose a tilted initial spin and step through one turn using the time control.",
  "Reverse the angular frequency. Compare the path and its direction.",
]);
const tilt=lab.range("tilt","Initial polar angle",0,180,5,60,"°");
const omega=lab.range("omega","Angular frequency",-4,4,0.25,1,"rad/s");
const start=lab.range("time","Start time",0,10,0.1,0,"s");
const output=["x","y","z"].map(key=>lab.result(key,"Spin component "+key,"",5));
const time=lab.result("elapsed","Lab time","s",3);
let t=0, theta=0, rate=0;
function draw() {
  const v=[Math.sin(theta)*Math.cos(rate*t),Math.sin(theta)*Math.sin(rate*t),Math.cos(theta)];
  v.forEach((component,i)=>output[i](component)); time(t);
  const {ctx,w,h}=prep($("bloch-plot"));
  const r=0.42*Math.min(w,h), cx=w/2, cy=h/2, angle=0.35;
  const project=([x,y,z])=>[cx+r*x,cy-r*(z*Math.cos(angle)+y*Math.sin(angle))];
  ctx.strokeStyle=tok("--muted"); ctx.lineWidth=1;
  ctx.beginPath(); ctx.arc(cx,cy,r,0,2*Math.PI); ctx.stroke();
  function ring(polar,color) {
    const points=Array.from({length:97},(_,i)=>{
      const a=i*Math.PI/48;
      return project([Math.sin(polar)*Math.cos(a),Math.sin(polar)*Math.sin(a),Math.cos(polar)]);
    });
    line(ctx,points,color,1,[3,3]);
  }
  ring(Math.PI/2,tok("--grid")); ring(theta,tok("--accent-2"));
  line(ctx,[project([0,0,-1]),project([0,0,1])],tok("--grid"));
  const tip=project(v);
  line(ctx,[[cx,cy],tip],tok("--accent"),3); dot(ctx,...tip,5,tok("--accent"));
}
function reset() { theta=tilt()*Math.PI/180; rate=omega(); t=start(); draw(); }
lab.start(reset,draw);
registerSim("bloch","bloch-play",dt=>{ t+=dt; },draw);
