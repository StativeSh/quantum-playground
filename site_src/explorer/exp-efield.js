import {$, experiment, prep, line, tok} from "./core.js";

const lab = experiment("efield", "Halfway between +q and −q, is E zero? Is V?", [
  "Place equal and opposite charges the same distance from the probe. Predict the field direction and potential.",
  "Change the negative charge to positive. Compare which quantities cancel.",
]);
const count = lab.range("count","Number of charges",1,4,1,2);
const sources = [[-0.5,0],[0.5,0],[0,0.5],[0,-0.5]].map(([x,y],i) => ({
  x: lab.range("x"+i,"Charge "+(i+1)+" x",-0.9,0.9,0.05,x,"m"),
  y: lab.range("y"+i,"Charge "+(i+1)+" y",-0.9,0.9,0.05,y,"m"),
  q: lab.range("q"+i,"Charge "+(i+1),-5,5,0.5,i%2 ? -1 : 1,"nC"),
}));
const probeX = lab.range("px","Probe x",-0.9,0.9,0.05,0,"m");
const probeY = lab.range("py","Probe y",-0.9,0.9,0.05,0,"m");
const ex = lab.result("ex","Horizontal electric field","N/C",3);
const ey = lab.result("ey","Vertical electric field","N/C",3);
const potential = lab.result("v","Electric potential","V",3);
const canvas = $("efield-plot");

function field(charges,x,y) {
  let fx=0, fy=0, v=0;
  for (const charge of charges) {
    const dx=x-charge.x, dy=y-charge.y, r=Math.hypot(dx,dy);
    if (!r || !charge.q) continue;
    const kq = 8.9875517862*charge.q; // k in SI times 1 nC
    v += kq/r;
    fx += kq*dx/r**3;
    fy += kq*dy/r**3;
  }
  return {fx,fy,v};
}
function update() {
  sources.forEach((source,i) => {
    for (const key of ["x","y","q"]) $("efield-"+key+i).closest(".control").hidden = i>=count();
  });
  const charges = sources.slice(0,count()).map(s => ({x:s.x(),y:s.y(),q:s.q()}));
  const probe = field(charges,probeX(),probeY());
  const singular = charges.some(c => c.q && c.x===probeX() && c.y===probeY());
  ex(singular ? "At point charge" : probe.fx);
  ey(singular ? "At point charge" : probe.fy);
  potential(singular ? "At point charge" : probe.v);
  const {ctx,w,h} = prep(canvas);
  const X = x => (x+1)*w/2, Y = y => (1-y)*h/2;
  const grid = 32;
  const levels = [-80,-40,-20,-10,0,10,20,40,80];
  const samples = Array.from({length:grid+1},(_,i) => Array.from({length:grid+1},(_,j) =>
    field(charges,2*i/grid-1,1-2*j/grid).v));
  // Interpolate equipotential crossings on each cell edge.
  ctx.strokeStyle=tok("--muted");
  ctx.lineWidth=0.8;
  ctx.beginPath();
  for (let i=0;i<grid;i++) for (let j=0;j<grid;j++) {
    const corners=[[i,j],[i+1,j],[i+1,j+1],[i,j+1]];
    for (const level of levels) {
      let first=true;
      corners.forEach(([ax,ay],k) => {
        const [bx,by]=corners[(k+1)%4], a=samples[ax][ay], b=samples[bx][by];
        if ((a<level)===(b<level)) return;
        const f=(level-a)/(b-a);
        const x=(ax+f*(bx-ax))*w/grid, y=(ay+f*(by-ay))*h/grid;
        if(first) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        first=!first;
      });
    }
  }
  ctx.stroke();
  const ink=tok("--fg"), scale=Math.min(w,h)/45;
  for (let i=0;i<13;i++) for (let j=0;j<13;j++) {
    const x=(i-6)/6.5, y=(j-6)/6.5, {fx,fy}=field(charges,x,y);
    const strength=Math.hypot(fx,fy);
    if (strength<1e-9) continue;
    const dx=scale*fx/strength, dy=-scale*fy/strength, tip=[X(x)+dx,Y(y)+dy];
    line(ctx,[[X(x)-dx,Y(y)-dy],tip,[tip[0]-0.55*dx+0.4*dy,tip[1]-0.55*dy-0.4*dx]],ink,1);
  }
  ctx.font="bold 14px system-ui";
  ctx.textAlign="center";
  ctx.textBaseline="middle";
  for(const {x,y,q} of charges) {
    ctx.fillStyle=tok(q<0 ? "--accent-2" : "--accent");
    ctx.beginPath(); ctx.arc(X(x),Y(y),11,0,2*Math.PI); ctx.fill();
    ctx.fillStyle=tok("--panel"); ctx.fillText(q<0 ? "−" : q>0 ? "+" : "0",X(x),Y(y));
  }
  ctx.strokeStyle=ink;
  ctx.lineWidth=2;
  ctx.strokeRect(X(probeX())-5,Y(probeY())-5,10,10);
}
let drag;
function position(event) {
  const r=canvas.getBoundingClientRect();
  return [2*(event.clientX-r.left)/r.width-1,1-2*(event.clientY-r.top)/r.height];
}
canvas.addEventListener("pointerdown", event => {
  const [x,y]=position(event);
  const handles=sources.slice(0,count()).map((s,i) => [s.x(),s.y(),"x"+i,"y"+i]);
  handles.push([probeX(),probeY(),"px","py"]);
  const nearest=handles.sort((a,b) => Math.hypot(a[0]-x,a[1]-y)-Math.hypot(b[0]-x,b[1]-y))[0];
  if (Math.hypot(nearest[0]-x,nearest[1]-y) > 36/canvas.clientWidth) return;
  drag=nearest.slice(2);
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", event => {
  if (!drag || !canvas.hasPointerCapture(event.pointerId)) return;
  const coords=position(event);
  drag.forEach((key,i) => {
    const input=$("efield-"+key);
    input.value=Math.round(coords[i]*20)/20;
    input.labels[0].querySelector("output").value=input.value+" m";
  });
  update();
});
canvas.addEventListener("lostpointercapture",() => { drag=null; });
lab.start(update);
