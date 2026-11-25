import {$, experiment, prep, registerSim, seededRandom, tok} from "./core.js";

const lab = experiment("decay", "After two half-lives, how many remain? Exactly that many?", [
  "Pause and reset the dice. Predict how many nuclei will survive two half-lives.",
  "Step to the nearest whole second. Compare the surviving count with the expected count, then repeat with a larger sample.",
]);
const initial = lab.range("initial", "Initial nuclei", 100, 1000, 100, 400);
const probability = lab.range("probability", "Decay probability per second", 0.05, 0.5, 0.05, 0.15);
const count = lab.result("count", "Surviving nuclei", "", 0);
const expected = lab.result("expected", "Expected survivors");
const elapsed = lab.result("time", "Elapsed time", "s", 0);
const half = lab.result("half", "Predicted half-life", "s", 3);
const observed = lab.result("observed", "Measured half-life", "s", 2);

let dirty = true;
let nuclei, random, survivors, seconds, accumulated, measured;
function draw() {
  dirty = false;
  const {ctx, w, h} = prep($("decay-plot"));
  const columns = Math.ceil(Math.sqrt(nuclei.length * w / h));
  const cell = Math.min(w / columns, h / Math.ceil(nuclei.length / columns));
  const live = tok("--accent"), gone = tok("--grid");
  for (let i = 0; i < nuclei.length; i++) {
    ctx.fillStyle = nuclei[i] ? live : gone;
    ctx.beginPath();
    ctx.arc((i % columns + 0.5) * cell, (Math.floor(i / columns) + 0.5) * cell, cell * 0.35, 0, 2*Math.PI);
    ctx.fill();
  }
}
function update() {
  const lambda = -Math.log1p(-probability());
  count(survivors);
  expected(initial() * Math.exp(-lambda * seconds));
  elapsed(seconds);
  half(Math.LN2 / lambda);
  observed(measured ?? "Awaiting half the sample");
  $("decay-step").disabled = survivors === 0;
  dirty = true;
}
function reset() {
  nuclei = new Uint8Array(initial()).fill(1);
  random = seededRandom(2026);
  survivors = initial();
  seconds = 0;
  accumulated = 0;
  measured = null;
  update();
}
function roll() {
  const before = survivors;
  for (let i = 0; i < nuclei.length; i++) {
    if (nuclei[i] && random() < probability()) {
      nuclei[i] = 0;
      survivors--;
    }
  }
  if (measured === null && survivors <= initial()/2) {
    measured = seconds + (before - initial()/2) / (before - survivors);
  }
  seconds++;
  if (survivors === 0) setPlaying(false);
  update();
  draw();
}
$("decay-step").addEventListener("click", roll);
$("decay-reset").addEventListener("click", () => { reset(); draw(); });
lab.start(reset, draw);
draw();
const setPlaying = registerSim("decay", "decay-play", dt => {
  if (!survivors) { setPlaying(false); return; }
  accumulated += dt;
  if (accumulated >= 1) {
    accumulated -= 1;
    roll();
  }
}, () => {
  if (dirty) draw();
});
