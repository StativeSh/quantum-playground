import {$, experiment, plot} from "./core.js";

const lab = experiment("projectile", "With air resistance, is 45° still the angle of greatest range?", [
  "Start on level ground. Compare the ranges at 35°, 40°, 45° and 50°.",
  "Switch on air resistance and repeat at the same speed. Which angle gives the longest range now?",
]);
const speed = lab.range("speed", "Launch speed", 5, 40, 1, 30, "m/s");
const angle = lab.range("angle", "Launch angle", 5, 85, 1, 45, "°");
const height = lab.range("height", "Launch height", 0, 10, 0.5, 0, "m");
const range = lab.result("range", "Horizontal range", "m");
const flight = lab.result("flight", "Time of flight", "s");
const peak = lab.result("peak", "Maximum height above ground", "m");

// Midpoint integration of a = -g ŷ - c |v| v. Interpolate the ground crossing.
function update() {
  const drag = $("projectile-drag").checked ? 0.02 : 0;
  const theta = angle() * Math.PI / 180;
  let vx = speed() * Math.cos(theta), vy = speed() * Math.sin(theta);
  let x = 0, y = height(), highest = y, t = 0;
  const path = [[x, y]], dt = 0.005;
  do {
    const damping = drag * Math.hypot(vx, vy);
    const midX = vx - dt / 2 * damping * vx;
    const midY = vy - dt / 2 * (9.81 + damping * vy);
    const midDamping = drag * Math.hypot(midX, midY);
    const dy = dt * midY;
    const fraction = y + dy < 0 ? -y / dy : 1;
    x += fraction * dt * midX;
    y = Math.max(0, y + fraction * dy);
    t += fraction * dt;
    highest = Math.max(highest, y);
    path.push([x, y]);
    if (fraction < 1) break;
    vx -= dt * midDamping * midX;
    vy -= dt * (9.81 + midDamping * midY);
  } while (y > 0);
  range(x);
  flight(t);
  peak(highest);
  plot($("projectile-plot"), {xLabel: "distance (m)", yLabel: "height (m)", series: [{points: path}]});
}
lab.start(update);
