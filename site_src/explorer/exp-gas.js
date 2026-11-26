import {$, experiment, plot, prep, registerSim, seededRandom, tok} from "./core.js";

const lab = experiment("gas", "At the same temperature, how does moving the piston change the pressure?", [
  "Measure 100 ps of wall impacts. Compare impulse per area per time with NkT/V.",
  "Halve the chamber width with the piston. Repeat the measurement and compare the speed distributions.",
]);
const number = lab.range("n", "Helium atoms", 100, 300, 10, 200);
const temperature = lab.range("temperature", "Temperature", 100, 600, 10, 300, "K");
const width = lab.range("width", "Piston position", 30, 90, 1, 60, "nm");
const seed = lab.range("seed", "Initial velocity seed", 0, 65535, 1, 903);
const pressure = lab.result("pressure", "Pressure from wall impacts", "kPa", 3);
const ideal = lab.result("ideal", "NkT/V", "kPa", 3);
const rms = lab.result("rms", "Sample rms speed", "m/s");
const peakDensity = lab.result("density", "Maxwell–Boltzmann peak density", "s/m", 7);
const elapsed = lab.result("time", "Observation time", "ps", 1);
const mass = 4.002602*1.66053906892e-27, kB = 1.380649e-23;
// Positions in nm; velocities in nm/ps (1 nm/ps = 1000 m/s).
const radius = 0.3, depth = 60;
let atoms, size, impulse, time, nextPlot;
function reset() {
  const n=number(), cells=Math.ceil(Math.cbrt(n)), random=seededRandom(seed());
  size=[width(),depth,depth];
  const thermal=Math.sqrt(kB*temperature()/mass)/1000;
  const gaussian=() => thermal*Math.sqrt(-2*Math.log(1-random()))*Math.cos(2*Math.PI*random());
  atoms=Array.from({length:n},(_,i) => ({
    p:[i%cells,Math.floor(i/cells)%cells,Math.floor(i/cells**2)].map((v,k) => (v+0.5)*size[k]/cells),
    v:[gaussian(),gaussian(),gaussian()],
  }));
  impulse=0;
  time=0;
  nextPlot=0;
  ideal(n*kB*temperature()/(size[0]*depth**2*1e-27)/1000);
  draw();
}
function substep(dt) {
  for (const {p,v} of atoms) {
    for (let k=0;k<3;k++) {
      p[k]+=dt*v[k];
      const limit=size[k]-radius;
      if (p[k]<radius || p[k]>limit) {
        p[k]=p[k]<radius ? 2*radius-p[k] : 2*limit-p[k];
        impulse+=2*mass*Math.abs(v[k])*1000;
        v[k]=-v[k];
      }
    }
  }
  // Sweep along x; only neighbours within one diameter can collide.
  atoms.sort((a,b) => a.p[0]-b.p[0]);
  for (let i=0;i<atoms.length;i++) {
    const a=atoms[i];
    for (let j=i+1;j<atoms.length;j++) {
      const b=atoms[j], dx=b.p[0]-a.p[0];
      if (dx>2*radius) break;
      const dy=b.p[1]-a.p[1], dz=b.p[2]-a.p[2], r2=dx*dx+dy*dy+dz*dz;
      if (r2 >= 4*radius**2 || r2 === 0) continue;
      const normalSpeed=((a.v[0]-b.v[0])*dx+(a.v[1]-b.v[1])*dy+(a.v[2]-b.v[2])*dz)/r2;
      if (normalSpeed<=0) continue;
      // Apply the equal and opposite impulses without allocating a vector
      // for each collision in the innermost loop.
      a.v[0]-=normalSpeed*dx; b.v[0]+=normalSpeed*dx;
      a.v[1]-=normalSpeed*dy; b.v[1]+=normalSpeed*dy;
      a.v[2]-=normalSpeed*dz; b.v[2]+=normalSpeed*dz;
    }
  }
  time+=dt;
}
function advance(ps) {
  // Short substeps resolve a diameter even for the high-speed tail.
  const steps=Math.ceil(ps/0.08);
  for (let i=0;i<steps;i++) substep(ps/steps);
}
function distribution() {
  const speeds=atoms.map(a => 1000*Math.hypot(...a.v));
  const sigma=Math.sqrt(kB*temperature()/mass);
  const top=Math.max(4.5*sigma,...speeds), bins=24, dv=top/bins;
  const counts=new Array(bins).fill(0);
  for (const v of speeds) counts[Math.min(bins-1,Math.floor(v/dv))]++;
  const histogram=counts.flatMap((n,i) => [[i*dv,n/(number()*dv)],[(i+1)*dv,n/(number()*dv)]]);
  const mb=v => Math.sqrt(2/Math.PI)*v**2/sigma**3*Math.exp(-0.5*(v/sigma)**2);
  peakDensity(mb(Math.SQRT2*sigma));
  const theory=Array.from({length:100},(_,i) => {
    const v=i*top/99;
    return [v,mb(v)];
  });
  plot($("gas-plot2"),{xLabel:"speed (m/s)",yLabel:"probability density (s/m)",series:[
    {points:histogram},{points:theory,dash:[5,3]},
  ]});
  rms(Math.sqrt(speeds.reduce((sum,v) => sum+v*v,0)/speeds.length));
  const area=2*(depth**2+2*depth*size[0])*1e-18;
  pressure(time ? impulse/(area*time*1e-12)/1000 : "Awaiting wall impacts");
  elapsed(time);
  nextPlot=time+2;
}
function draw() {
  const {ctx,w,h}=prep($("gas-plot"));
  const ink=tok("--accent"), left=5, scale=Math.min((w-10)/90,(h-10)/depth);
  ctx.strokeStyle=tok("--fg");
  ctx.strokeRect(left,5,size[0]*scale,depth*scale);
  ctx.fillStyle=tok("--accent-2");
  ctx.fillRect(left+size[0]*scale-2,5,4,depth*scale);
  ctx.fillStyle=ink;
  ctx.beginPath();
  for (const {p} of atoms) {
    const x=left+p[0]*scale, y=5+p[1]*scale, r=Math.max(1.4,radius*scale);
    ctx.moveTo(x+r,y);
    ctx.arc(x,y,r,0,2*Math.PI);
  }
  ctx.fill();
  if (time>=nextPlot) distribution();
}
lab.start(reset,() => { nextPlot=0; draw(); });
$("gas-sample").addEventListener("click",() => { advance(100); nextPlot=0; draw(); });
registerSim("gas","gas-play",dt => advance(30*dt),draw);
