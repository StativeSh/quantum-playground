import {$, experiment, plot} from "./core.js";

const lab = experiment("fourier", "As you add harmonics, what happens to the height and width of the first overshoot?", [
  "Start with one odd harmonic. Double the number of terms and compare the peak with the edge of the square wave.",
  "Move the probe toward the jump and compare the series with the target on either side.",
]);
const terms = lab.range("terms","Odd harmonics",1,40,1,5);
const period = lab.range("period","Period",1,6,0.5,2,"s");
const probe = lab.range("probe","Probe position / period",-0.5,0.5,0.005,0.125);
const value = lab.result("value","Series at probe","",6);
const overshoot = lab.result("overshoot","Overshoot / jump","%",4);
const peakTime = lab.result("peak","First peak after jump","s",5);
function update() {
  const n=terms(), T=period();
  function sum(phase) {
    let y=0;
    for(let k=1;k<2*n;k+=2) y+=4*Math.sin(2*Math.PI*k*phase)/(Math.PI*k);
    return y;
  }
  const peak=1/(4*n); // first zero of the sum of odd cosines
  value(sum(probe())); overshoot(50*(sum(peak)-1)); peakTime(peak*T);
  const points=Array.from({length:801},(_,i) => {
    const f=i/800-0.5;
    return [f*T,sum(f)];
  });
  plot($("fourier-plot"),{xLabel:"time (s)",yLabel:"amplitude",series:[
    {points:[[-T/2,-1],[0,-1],[0,1],[T/2,1]],dash:[3,4]},
    {points},{points:[[probe()*T,sum(probe())]]},
  ]});
}
lab.start(update);
