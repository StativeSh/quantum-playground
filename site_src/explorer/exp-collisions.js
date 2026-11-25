import {$, experiment, prep, registerSim, tok} from "./core.js";

const lab = experiment("collisions", "Equal masses, elastic, one at rest: what happens?", [
  "Set both masses to 1 kg, restitution to 1 and the second velocity to zero. Predict each velocity after impact.",
  "Watch the carts pass momentum between them. Reduce restitution and compare the total kinetic energies.",
]);
const mass1 = lab.range("mass1", "Cart 1 mass", 0.5, 4, 0.5, 1, "kg");
const mass2 = lab.range("mass2", "Cart 2 mass", 0.5, 4, 0.5, 1, "kg");
const speed1 = lab.range("u1", "Cart 1 velocity", -3, 3, 0.5, 2, "m/s");
const speed2 = lab.range("u2", "Cart 2 velocity", -3, 3, 0.5, 0, "m/s");
const restitution = lab.range("restitution", "Coefficient of restitution", 0, 1, 0.1, 1);
const first = lab.result("v1", "Cart 1 final velocity", "m/s", 3);
const second = lab.result("v2", "Cart 2 final velocity", "m/s", 3);
const momentumBefore = lab.result("p-before", "Initial momentum", "kg m/s", 3);
const momentumAfter = lab.result("p-after", "Final momentum", "kg m/s", 3);
const energyBefore = lab.result("k-before", "Initial kinetic energy", "J", 3);
const energyAfter = lab.result("k-after", "Final kinetic energy", "J", 3);

let t, u1, u2, v1, v2, gap;
function positions(time) {
  // For closing carts, the front edges meet at t = 1 s.
  const approach = Math.min(1, time), after = Math.max(0, time - 1);
  return [approach*u1 + after*v1, gap + approach*u2 + after*v2];
}
function draw() {
  const {ctx, w, h} = prep($("collisions-plot"));
  const endpoints = [0, gap, ...positions(1), ...positions(3)];
  const low = Math.min(...endpoints), high = Math.max(...endpoints);
  const width = Math.min(50, w/7);
  const X = x => width + 8 + (w - 2*width - 16) * (x - low) / (high - low);
  const [left, right] = positions(t);
  const y = h/2;
  ctx.fillStyle = tok("--grid");
  ctx.fillRect(0, y+27, w, 3);
  function cart(x, label, color) {
    ctx.fillStyle = tok(color);
    ctx.fillRect(x, y, width, 22);
    ctx.fillStyle = tok("--fg");
    for (const wheel of [0.2, 0.8]) {
      ctx.beginPath();
      ctx.arc(x + wheel*width, y+23, 4, 0, 2*Math.PI);
      ctx.fill();
    }
    ctx.textAlign = "center";
    ctx.font = "14px system-ui";
    ctx.fillText(label, x + width/2, y - 6);
  }
  cart(X(left)-width, "1", "--accent");
  cart(X(right), "2", "--accent-2");
}
function reset() {
  t = 0;
  const m1 = mass1(), m2 = mass2();
  u1 = speed1();
  u2 = speed2();
  gap = u1 > u2 ? u1 - u2 : 1;
  const impulse = (1 + restitution()) * Math.max(0, u1 - u2) / (1/m1 + 1/m2);
  v1 = u1 - impulse/m1;
  v2 = u2 + impulse/m2;
  first(v1);
  second(v2);
  momentumBefore(m1*u1 + m2*u2);
  momentumAfter(m1*v1 + m2*v2);
  energyBefore((m1*u1**2 + m2*u2**2)/2);
  energyAfter((m1*v1**2 + m2*v2**2)/2);
}
lab.start(reset, draw);
draw();
registerSim("collisions", "collisions-play", dt => { t = (t + dt) % 3; }, draw);
