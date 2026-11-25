import {$, experiment, prep, line, tok} from "./core.js";

const lab = experiment("launch", "Is the escape speed different if you launch sideways rather than straight up?", [
  "Raise the speed until the path is unbound. Compare vertical and horizontal launches.",
  "Change the planet mass while keeping its radius fixed. Compare the circular and escape speeds.",
]);
const speed = lab.range("speed","Launch speed / circular speed",0,2,0.01,1);
const angle = lab.range("angle","Elevation above horizontal",0,90,1,0,"°");
const mass = lab.range("mass","Planet mass",1,10,0.1,5.9,"× 10²⁴ kg");
const radius = lab.range("radius","Planet radius",2,10,0.1,6.4,"× 10⁶ m");
const circular = lab.result("circular","Circular speed","km/s",4);
const escape = lab.result("escape","Escape speed","km/s",4);
const launch = lab.result("velocity","Launch speed","km/s",4);
const fate = lab.result("fate","Outcome");
function update() {
  const vc = Math.sqrt(6.67430e-11*mass()*1e24/(radius()*1e6))/1000;
  circular(vc);
  escape(Math.SQRT2*vc);
  launch(speed()*vc);
  fate(speed() >= Math.SQRT2 ? "Escapes" : angle() === 0 && speed() >= 1 ? "Orbits" : "Falls back");
  // Velocity Verlet in units R = GM = 1; stop at the surface or beyond the view.
  const dt = 0.015, theta = angle()*Math.PI/180;
  let x = 0, y = 1, vx = speed()*Math.cos(theta), vy = speed()*Math.sin(theta);
  const points = [[x,y]];
  for (let i=0; i<2000; i++) {
    const r = Math.hypot(x,y);
    vx -= dt*x/(2*r**3);
    vy -= dt*y/(2*r**3);
    x += dt*vx;
    y += dt*vy;
    const next = Math.hypot(x,y);
    points.push([x,y]);
    if (next < 1-1e-8 || next > 5) break;
    vx -= dt*x/(2*next**3);
    vy -= dt*y/(2*next**3);
  }
  const {ctx,w,h} = prep($("launch-plot"));
  const extent = Math.max(...points.map(([x,y]) => Math.hypot(x,y)));
  const scale = 0.46*Math.min(w,h)/extent;
  ctx.fillStyle = tok("--grid");
  ctx.beginPath();
  ctx.arc(w/2,h/2,scale,0,2*Math.PI);
  ctx.fill();
  line(ctx,points.map(([x,y]) => [w/2+x*scale,h/2-y*scale]),tok("--accent"));
}
lab.start(update);
