import {$, experiment, prep, line, dot, tok, registerSim} from "./core.js";

const lab=experiment("double-pendulum","How long do two nearby starting configurations stay together?",[
  "Pause and compare the lower bobs with a small initial angle offset. Scrub forward in time.",
  "Repeat with larger starting angles. Compare separation at the same elapsed time.",
]);
const upper=lab.range("upper","Initial upper angle",-170,170,5,100,"°");
const lower=lab.range("lower","Initial lower angle",-170,170,5,90,"°");
const offset=lab.range("offset","Offset of second lower rod",0,5,0.1,0.5,"°");
const start=lab.range("time","Start time",0,10,0.1,0,"s");
const first=lab.result("theta1","Upper angle, system A","rad",6);
const second=lab.result("theta2","Lower angle, system A","rad",6);
const gap=lab.result("gap","Lower bob separation","m",6);
const elapsed=lab.result("elapsed","Elapsed time","s",3);
const radians=Math.PI/180, g=9.81;
let a,b,t,trailA,trailB;
function derivative([u,l,wu,wl]) {
  const d=u-l,s=Math.sin(d),c=Math.cos(d),den=3-Math.cos(2*d);
  return [wu,wl,(-3*g*Math.sin(u)-g*Math.sin(u-2*l)-2*s*(wl*wl+wu*wu*c))/den,
    2*s*(2*wu*wu+2*g*Math.cos(u)+wl*wl*c)/den];
}
function stepState(state,h) {
  const mid=(k,dt)=>state.map((v,i)=>v+dt*k[i]);
  const k1=derivative(state),k2=derivative(mid(k1,h/2)),k3=derivative(mid(k2,h/2)),k4=derivative(mid(k3,h));
  return state.map((v,i)=>v+h*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);
}
function tip([u,l]) { return [Math.sin(u)+Math.sin(l),Math.cos(u)+Math.cos(l)]; }
function advance(dt) {
  const n=Math.ceil(dt/0.003);
  for(let i=0;i<n;i++) {
    a=stepState(a,dt/n); b=stepState(b,dt/n);
    if (i%8===0) { trailA.push(tip(a)); trailB.push(tip(b)); }
  }
  trailA=trailA.slice(-180); trailB=trailB.slice(-180);
  t+=dt;
}
function draw() {
  const {ctx,w,h}=prep($("double-pendulum-plot")),scale=Math.min(w/9,h/4.5);
  const left=tip(a),right=tip(b);
  first(a[0]); second(a[1]); elapsed(t); gap(Math.hypot(left[0]-right[0],left[1]-right[1]));
  function rods(state,trail,cx,color) {
    const X=x=>cx+x*scale,Y=y=>h/2+y*scale;
    const joint=[X(Math.sin(state[0])),Y(Math.cos(state[0]))], end=tip(state);
    line(ctx,trail.map(([x,y])=>[X(x),Y(y)]),color,1,[2,3]);
    line(ctx,[[cx,Y(0)],joint,[X(end[0]),Y(end[1])]],color,2.5);
    dot(ctx,...joint,4,color);dot(ctx,X(end[0]),Y(end[1]),5,color);
  }
  rods(a,trailA,w/4,tok("--accent")); rods(b,trailB,3*w/4,tok("--accent-2"));
}
function reset() {
  a=[upper()*radians,lower()*radians,0,0];
  b=[a[0],(lower()+offset())*radians,0,0]; t=0; trailA=[]; trailB=[];
  advance(start()); draw();
}
lab.start(reset,draw);
registerSim("double-pendulum","double-pendulum-play",advance,draw);
