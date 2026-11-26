import {$, experiment, prep, axes, line, tok} from "./core.js";

const lab=experiment("phase-portrait","Which changes turn a closed phase orbit into a spiral or a saddle?",[
  "Start with positive stiffness and zero damping. Follow a trajectory from the marked initial displacement.",
  "Change damping through zero, then reverse the sign of stiffness. Relate the arrows to the fixed-point classification.",
]);
const stiffness=lab.range("k","Stiffness k",-2,4,0.25,1);
const damping=lab.range("b","Damping b",-2,4,0.25,0.5);
const initial=lab.range("x","Initial displacement",-1.5,1.5,0.1,1);
const velocity=lab.range("v","Initial velocity",-1.5,1.5,0.1,0);
const kind=lab.result("kind","Origin");
const trace=lab.result("trace","Jacobian trace","",3);
const determinant=lab.result("det","Jacobian determinant","",3);
const acceleration=lab.result("accel","Initial acceleration","",4);
function update() {
  const k=stiffness(),b=damping(), tau=-b;
  let type;
  if (k===0) type="degenerate";
  else if (k<0) type="saddle";
  else if (tau===0) type="center";
  else type=(tau<0 ? "stable " : "unstable ")+(tau*tau<4*k ? "spiral" : "node");
  kind(type);trace(tau);determinant(k);acceleration(-k*initial()-b*velocity());
  const {ctx,w,h}=prep($("phase-portrait-plot"));
  const {X,Y,pad}=axes(ctx,w,h,[-2,2],[-2,2],{xlabel:"displacement x",ylabel:"velocity y"});
  ctx.save();ctx.beginPath();ctx.rect(pad.l,pad.t,w-pad.l-pad.r,h-pad.t-pad.b);ctx.clip();
  const ink=tok("--muted");
  for(let i=-6;i<=6;i++) for(let j=-6;j<=6;j++) {
    const x=i/3,y=j/3,a=-k*x-b*y;
    const dx=X(x+y)-X(x),dy=Y(y+a)-Y(y),mag=Math.hypot(dx,dy);
    if(!mag) continue;
    const u=dx/mag,v=dy/mag, tip=[X(x)+4*u,Y(y)+4*v];
    line(ctx,[[X(x)-4*u,Y(y)-4*v],tip,[tip[0]-3*u-2*v,tip[1]-3*v+2*u]],ink,1);
  }
  let x=initial(),y=velocity();
  const points=[[X(x),Y(y)]],dt=0.01;
  for(let i=0;i<1600 && Math.max(Math.abs(x),Math.abs(y))<=2.5;i++) {
    const mx=x+dt*y/2,my=y+dt*(-k*x-b*y)/2;
    x+=dt*my; y+=dt*(-k*mx-b*my); points.push([X(x),Y(y)]);
  }
  line(ctx,points,tok("--accent"),2);
  ctx.restore();
}
lab.start(update);
