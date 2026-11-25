import {$, experiment, prep, axes, line, plot, tok} from "./core.js";

const lab=experiment("logistic","When does one long-term population split into two?",[
  "Move r through 3. Compare alternate generations after the transient.",
  "Follow the highlighted slice across the branching diagram. Does a large growth parameter always produce chaos?",
]);
const rate=lab.range("r","Growth parameter r",2.5,4,0.005,3.2);
const initial=lab.range("initial","Initial population fraction",0.05,0.95,0.05,0.2);
const generation=lab.range("n","Generation",1,80,1,20);
const value=lab.result("value","Population at selected generation","",7);
const low=lab.result("min","Minimum after transient","",6);
const high=lab.result("max","Maximum after transient","",6);
function attractor(r,x) {
  for (let i=0;i<500;i++) x=r*x*(1-x);
  return Array.from({length:64},()=>{ x=r*x*(1-x); return x; });
}
let lastInitial, columns;
function update() {
  const r=rate(), x0=initial(), n=generation();
  let x=x0;
  const points=[[0,x]];
  for (let i=1;i<=80;i++) { x=r*x*(1-x); points.push([i,x]); }
  value(points[n][1]);
  plot($("logistic-plot"),{xLabel:"generation",yLabel:"population fraction",series:[{points},{points:[points[n]]}]});
  const visible=attractor(r,x0);
  low(Math.min(...visible)); high(Math.max(...visible));
  if (lastInitial!==x0) {
    columns=Array.from({length:401},(_,i)=>{
      const parameter=2.5+1.5*i/400;
      return [parameter,attractor(parameter,x0)];
    });
    lastInitial=x0;
  }
  const {ctx,w,h}=prep($("logistic-plot2"));
  const {X,Y}=axes(ctx,w,h,[2.5,4],[0,1],{xlabel:"growth parameter r",ylabel:"attracting populations"});
  ctx.fillStyle=tok("--accent");
  for(const [parameter,values] of columns) {
    const px=X(parameter);
    for (const v of values) ctx.fillRect(px,Y(v),1.6,1.2);
  }
  line(ctx,[[X(r),Y(0)],[X(r),Y(1)]],tok("--accent-2"),1.5);
}
lab.start(update);
