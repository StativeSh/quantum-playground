import { extension, plot, $, tok, fmt, prep, axes, line, onRedraw } from "./core.js";

function drawCoil() {
  const angle = Number($("coil-angle").value);
  const emf = deg => 2 * Math.sin(deg * Math.PI / 180);
  $("coil-angle-out").textContent = angle + "°";
  $("coil-flux").textContent = fmt(0.2 * Math.cos(angle * Math.PI / 180)) + " Wb turns";
  $("coil-emf").textContent = fmt(emf(angle)) + " V";
  const {ctx, w, h} = prep($("coil-plot"));
  const {X, Y} = axes(ctx, w, h, [0, 360], [-2.2, 2.2], {xlabel: "angle (°)", ylabel: "emf (V)"});
  const curve = Array.from({length: 181}, (_, i) => [X(2*i), Y(emf(2*i))]);
  line(ctx, curve, tok("--accent"), 2);
  ctx.fillStyle = tok("--accent-2");
  ctx.beginPath(); ctx.arc(X(angle), Y(emf(angle)), 5, 0, 2*Math.PI); ctx.fill();
}
$("coil-angle").addEventListener("input", drawCoil);

drawCoil();
onRedraw(drawCoil);

extension("rod", "As a rod slows on conducting rails, where does its kinetic energy go?", [
  "Set the starting speed, advance time and compare the energy lost with heat in the resistor.",
  "Double the field strength. Predict how long the speed will take to fall by the same fraction.",
], "Speed of the magnetically braked rod over time", (lab,canvas) => {
  const mass=lab.range("mass","Rod mass",0.1,1,0.1,0.2,"kg");
  const field=lab.range("field","Magnetic field",0.1,1,0.1,0.5,"T");
  const length=lab.range("length","Rail separation",0.2,1,0.1,0.5,"m");
  const resistance=lab.range("resistance","Resistance",0.5,5,0.5,1,"Ω");
  const initial=lab.range("initial","Starting speed",1,10,1,4,"m/s");
  const time=lab.range("time","Elapsed time",0,10,0.1,1,"s");
  const decay=lab.result("tau","Braking time constant","s",4);
  const speed=lab.result("speed","Rod speed","m/s",4);
  const loss=lab.result("lost","Kinetic energy lost","J",4);
  const heat=lab.result("heat","Heat in resistor","J",4);
  return () => {
    const m=mass(), bl=field()*length(), r=resistance(), v0=initial();
    const tau=m*r/bl**2, t=time(), v=v0*Math.exp(-t/tau);
    decay(tau); speed(v); loss(m*(v0*v0-v*v)/2);
    // Integral of I²R with I(t) = BLv(t)/R.
    heat((bl*v0)**2/r*tau/2*(-Math.expm1(-2*t/tau)));
    const points=Array.from({length:151},(_,i) => [i/15,v0*Math.exp(-i/(15*tau))]);
    plot(canvas,{xLabel:"time (s)",yLabel:"speed (m/s)",series:[{points},{points:[[t,v]]}]});
  };
});
