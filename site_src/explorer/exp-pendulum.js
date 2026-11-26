import { extension, plot, $, tok, fmt, prep, axes, line, dot, onRedraw, registerSim } from "./core.js";

// ---------- pendulum ----------
const g = 9.81;
function ellipK(m) {                       // complete elliptic integral of the first kind, via the AGM
  let a = 1, b = Math.sqrt(1 - m);
  for (let i = 0; i < 40 && Math.abs(a - b) > 1e-15; i++) { const an = (a + b) / 2; b = Math.sqrt(a * b); a = an; }
  return Math.PI / (2 * a);
}
const period = (th0, L) => 4 * Math.sqrt(L / g) * ellipK(Math.sin(th0 / 2) ** 2);
const pend = { th: 0, om: 0, t: 0, th0: 0, L: 1 };

function pendParams() {
  pend.th0 = +$("pend-amp").value * Math.PI / 180;
  pend.L = +$("pend-len").value;
  pend.th = pend.th0; pend.om = 0; pend.t = 0;
  const T = period(pend.th0, pend.L), T0 = 2 * Math.PI * Math.sqrt(pend.L / g);
  $("pend-amp-out").textContent = `${$("pend-amp").value}°`;
  $("pend-len-out").textContent = `${pend.L.toFixed(2)} m`;
  $("pend-T").textContent = `${fmt(T)} s`;
  $("pend-T0").textContent = `${fmt(T0)} s`;
  $("pend-ratio").textContent = `${fmt(T / T0)} ×`;
  drawPendCurve();
}
function stepPend(dt) {                    // RK4 with 1 ms substeps
  const k = g / pend.L, n = Math.max(1, Math.ceil(dt / 0.001)), h = dt / n;
  for (let i = 0; i < n; i++) {
    const f = (th, om) => [om, -k * Math.sin(th)];
    const [a1, b1] = f(pend.th, pend.om);
    const [a2, b2] = f(pend.th + h / 2 * a1, pend.om + h / 2 * b1);
    const [a3, b3] = f(pend.th + h / 2 * a2, pend.om + h / 2 * b2);
    const [a4, b4] = f(pend.th + h * a3, pend.om + h * b3);
    pend.th += h / 6 * (a1 + 2 * a2 + 2 * a3 + a4);
    pend.om += h / 6 * (b1 + 2 * b2 + 2 * b3 + b4);
  }
  pend.t += dt;
}
function drawPend() {
  const { ctx, w, h } = prep($("pend-anim"));
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.42;   // whole circle visible: amplitudes past 90° swing above the pivot
  const thSmall = pend.th0 * Math.cos(Math.sqrt(g / pend.L) * pend.t);
  ctx.strokeStyle = tok("--grid"); ctx.lineWidth = 1; ctx.setLineDash([2, 4]);
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]);
  const bob = (th) => [cx + R * Math.sin(th), cy + R * Math.cos(th)];
  const [sx, sy] = bob(thSmall), [ex, ey] = bob(pend.th);
  line(ctx, [[cx, cy], [sx, sy]], tok("--accent-2"), 1.5, [5, 4]);
  dot(ctx, sx, sy, 7, tok("--accent-2"));
  line(ctx, [[cx, cy], [ex, ey]], tok("--accent"), 2.5);
  dot(ctx, ex, ey, 9, tok("--accent"));
  dot(ctx, cx, cy, 3, tok("--fg"));
  ctx.fillStyle = tok("--muted"); ctx.font = `12px ${tok("--font-mono")}`;
  ctx.textAlign = "left"; ctx.textBaseline = "top";
  ctx.fillText(`t = ${pend.t.toFixed(1)} s`, 8, 8);
}
function drawPendCurve() {
  const { ctx, w, h } = prep($("pend-curve"));
  const pts = [];
  for (let d = 1; d <= 178; d += 1) pts.push([d, period(d * Math.PI / 180, 1) / (2 * Math.PI * Math.sqrt(1 / g))]);
  const ymax = Math.max(3.6, pts[pts.length - 1][1] * 1.02);
  const { X, Y } = axes(ctx, w, h, [0, 180], [1, ymax], { xlabel: "amplitude (°)", ylabel: "T / T₀", nx: 6, ny: 5, l: 40 });
  line(ctx, pts.map(([x, y]) => [X(x), Y(y)]), tok("--accent"), 2);
  const deg = +$("pend-amp").value, r = period(deg * Math.PI / 180, 1) / (2 * Math.PI * Math.sqrt(1 / g));
  line(ctx, [[X(deg), Y(1)], [X(deg), Y(r)]], tok("--accent-2"), 1, [3, 3]);
  dot(ctx, X(deg), Y(r), 5, tok("--accent-2"));
}
["pend-amp", "pend-len"].forEach((id) => $(id).addEventListener("input", pendParams));

pendParams();
drawPend();
registerSim("pend", "pend-play", stepPend, drawPend);
onRedraw(() => { drawPendCurve(); drawPend(); });

extension("spring", "How does damping change the height and width of the resonance peak?", [
  "Set a driving acceleration and sweep the drive frequency through the natural frequency.",
  "Increase damping and compare the peak and Q. Use the time slider to compare kinetic and elastic energy.",
], "Steady-state amplitude against angular driving frequency", (lab, canvas) => {
  const omega=lab.range("omega","Natural angular frequency",1,5,0.1,2,"rad/s");
  const gamma=lab.range("gamma","Damping rate",0.05,1,0.05,0.2,"s⁻¹");
  const force=lab.range("force","Driving acceleration",0,2,0.1,1,"m/s²");
  const drive=lab.range("drive","Driving angular frequency",0,8,0.1,2,"rad/s");
  const time=lab.range("time","Elapsed time",0,12,0.1,2,"s");
  const q=lab.result("q","Quality factor Q","",3);
  const displacement=lab.result("x","Displacement","m",4);
  const velocity=lab.result("v","Velocity","m/s",4);
  const kinetic=lab.result("ke","Kinetic energy (1 kg mass)","J",4);
  const potential=lab.result("pe","Elastic energy","J",4);
  const meters=["Kinetic energy","Elastic energy"].map(label => {
    const container=document.createElement("label"), meter=document.createElement("meter");
    container.append(label+" ",meter);
    $("spring").querySelector(".results").append(container);
    return meter;
  });
  return () => {
    const w=omega(), damping=gamma(), F=force(), W=drive(), end=time();
    const accel=(t,x,v) => F*Math.cos(W*t)-2*damping*v-w*w*x;
    let x=1, v=0;
    const n=Math.max(1,Math.ceil(end/0.01)), h=end/n;
    for(let i=0;i<n;i++) {
      const t=i*h, a1=accel(t,x,v);
      const v2=v+h*a1/2, a2=accel(t+h/2,x+h*v/2,v2);
      const v3=v+h*a2/2, a3=accel(t+h/2,x+h*v2/2,v3);
      const v4=v+h*a3, a4=accel(t+h,x+h*v3,v4);
      x+=h*(v+2*v2+2*v3+v4)/6;
      v+=h*(a1+2*a2+2*a3+a4)/6;
    }
    const K=v*v/2, U=(w*x)**2/2;
    displacement(x); velocity(v); kinetic(K); potential(U); q(w/(2*damping));
    meters.forEach((meter,i) => { meter.max=Math.max(1,K+U); meter.value=i ? U : K; });
    const amplitude=f => F/Math.hypot(w*w-f*f,2*damping*f);
    const points=Array.from({length:401},(_,i) => [i/50,amplitude(i/50)]);
    plot(canvas,{xLabel:"drive (rad/s)",yLabel:"steady amplitude (m)",series:[{points},{points:[[W,amplitude(W)]]}]});
  };
});
