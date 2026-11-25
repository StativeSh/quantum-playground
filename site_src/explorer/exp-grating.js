import { extension, plot, $, tok, fmt, prep, line, onRedraw } from "./core.js";

function drawGrating() {
  const density = Number($("grating-density").value);
  const ratio = density / 2000; // wavelength divided by grating period
  const limit = Math.floor(2000 / density);
  $("grating-density-out").textContent = density + " lines/mm";
  $("grating-angle").textContent = fmt(Math.asin(ratio) * 180 / Math.PI, 2) + "°";
  $("grating-count").textContent = 2 * limit + 1;
  const {ctx, w, h} = prep($("grating-plot"));
  const radius = Math.min(w/2 - 10, h - 34);
  const origin = [w/2, h-12];
  for (let m = -limit; m <= limit; m++) {
    const angle = Math.asin(Math.max(-1, Math.min(1, m * ratio)));
    line(ctx, [origin, [origin[0]+radius*Math.sin(angle), origin[1]-radius*Math.cos(angle)]], tok("--accent"), 2);
  }
}
$("grating-density").addEventListener("input", drawGrating);

drawGrating();
onRedraw(drawGrating);

extension("white", "How can you tell overlapping orders apart, and what changes when you add slits?", [
  "Compare the first red and blue maxima. Inspect higher orders for overlap.",
  "Increase the number of illuminated slits and compare peak widths at fixed line density.",
], "White-light diffraction across the screen, with three representative wavelength profiles", (lab,canvas) => {
  const nSlits=lab.range("slits","Illuminated slits",2,30,1,5);
  const density=lab.range("density","Lines per millimetre",200,1200,10,400);
  const blue=lab.result("blue","First blue maximum (450 nm)","°",3);
  const red=lab.result("red","First red maximum (650 nm)","°",3);
  const width=lab.result("width","Central green peak, zero-to-zero","°",3);
  const degrees=180/Math.PI;
  return () => {
    const d=1e-3/density(), n=nSlits();
    blue(degrees*Math.asin(450e-9/d)); red(degrees*Math.asin(650e-9/d));
    width(2*degrees*Math.asin(550e-9/(n*d)));
    const wavelengths=[450,550,650], colors=["#5681ff","#419a50","#dc533e"];
    // Sum mutually incoherent wavelengths. Each colour follows the N-slit intensity.
    function intensity(angle,lambda) {
      const phase=Math.PI*d*Math.sin(angle/degrees)/(lambda*1e-9);
      return Math.abs(Math.sin(phase))<1e-10 ? 1 : (Math.sin(n*phase)/(n*Math.sin(phase)))**2;
    }
    const series=wavelengths.map((nm,k) => ({color:colors[k],points:Array.from({length:1601},(_,i) => {
      const a=(i-800)/10;
      return [a,intensity(a,nm)];
    })}));
    plot(canvas,{xLabel:"angle (°)",yLabel:"relative intensity",series});
    const {width:w,height:h}=canvas.getBoundingClientRect(), ctx=canvas.getContext("2d");
    const band=ctx.createLinearGradient(46,0,w-12,0);
    for(let i=0;i<=360;i++) {
      const angle=(i/360-0.5)*160;
      const rgb=[0,0,0];
      for(let nm=400;nm<=700;nm+=5) {
        const value=intensity(angle,nm);
        for(const [k,center] of [620,540,450].entries()) rgb[k]+=value*Math.exp(-0.5*((nm-center)/34)**2);
      }
      band.addColorStop(i/360,"rgb("+rgb.map(c => Math.min(255,255*Math.sqrt(c/17))).join(",")+")");
    }
    ctx.fillStyle=band;
    ctx.fillRect(46,h-54,w-58,14);
  };
});
