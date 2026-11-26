import {$, experiment, prep, tok} from "./core.js";

const lab=experiment("hydrogen","How can you distinguish a radial node from an angular node in a density slice?",[
  "Compare 2s and 2p at the same scale. Move the probe from the centre outwards, then across the equator.",
  "Choose n = 3 and vary ℓ and |m|. Look for rings and nodal directions.",
]);
const principal=lab.range("n","Principal quantum number n",1,4,1,2);
const orbital=lab.range("l","Orbital quantum number ℓ",0,1,1,1);
const magnetic=lab.range("m","Magnetic quantum number m",-1,1,1,0);
const probeX=lab.range("x","Probe x",-16,16,0.25,0,"a₀");
const probeZ=lab.range("z","Probe z",-16,16,0.25,2,"a₀");
const density=lab.result("density","Probability density at probe","a₀⁻³",9);
const radial=lab.result("nodes","Radial nodes","",0);
const angular=lab.result("angular","Angular nodes","",0);
const raster=document.createElement("canvas");
raster.width=raster.height=111;
const factorial=[1];
for(let i=1;i<=8;i++) factorial[i]=i*factorial[i-1];

function restrict(key,min,max) {
  const input=$("hydrogen-"+key);
  input.min=min; input.max=max;
  input.labels[0].querySelector("output").value=input.value;
}
// Generalised Laguerre and associated Legendre recurrences; phase cancels in |ψ|².
function orbitalDensity(n,l,m) {
  const order=Math.abs(m), degree=n-l-1, alpha=2*l+1;
  const norm=(2/n)**3*factorial[degree]/(2*n*factorial[n+l])*
    (2*l+1)/(4*Math.PI)*factorial[l-order]/factorial[l+order];
  return (x,z) => {
    const r=Math.hypot(x,z), rho=2*r/n, u=r ? z/r : 1;
    let prev=0, lag=1;
    for(let j=1;j<=degree;j++) {
      const next=((2*j-1+alpha-rho)*lag-(j-1+alpha)*prev)/j;
      prev=lag; lag=next;
    }
    let leg=1;
    for(let j=1;j<=order;j++) leg*=-(2*j-1)*Math.sqrt(Math.max(0,1-u*u));
    prev=0;
    for(let j=order+1;j<=l;j++) {
      const next=((2*j-1)*u*leg-(j+order-1)*prev)/(j-order);
      prev=leg; leg=next;
    }
    return norm*Math.exp(-rho)*(rho**l*lag*leg)**2;
  };
}
let lastKey="";
function update() {
  const n=principal(); restrict("l",0,n-1);
  const l=orbital(); restrict("m",-l,l);
  const m=magnetic(), f=orbitalDensity(n,l,m), span=Math.max(16,2.2*n*n+3);
  density(f(probeX(),probeZ())); radial(n-l-1); angular(l);
  const key=[n,l,Math.abs(m)].join(",");
  if (lastKey!==key) {
    const N=raster.width, values=new Float64Array(N*N);
    let max=0;
    for(let j=0;j<N;j++) for(let i=0;i<N;i++) {
      const v=f((2*i/(N-1)-1)*span,(1-2*j/(N-1))*span);
      values[j*N+i]=v; max=Math.max(max,v);
    }
    const ctx=raster.getContext("2d"), img=ctx.createImageData(N,N);
    values.forEach((v,i)=>{
      const level=Math.sqrt(v/max); // square-root brightness exposes faint lobes
      img.data.set([10+80*level,19+175*level,33+218*level,255],4*i);
    });
    ctx.putImageData(img,0,0); lastKey=key;
  }
  const {ctx,w,h}=prep($("hydrogen-plot")), size=Math.min(w,h), left=(w-size)/2;
  ctx.drawImage(raster,left,0,size,size);
  const x=left+(1+probeX()/span)*size/2,y=(1-probeZ()/span)*size/2;
  ctx.strokeStyle="white";ctx.lineWidth=1.5;ctx.strokeRect(x-4,y-4,8,8);
  ctx.fillStyle=tok("--fg");ctx.font="12px system-ui";ctx.fillText("z ↑   x →",4,14);
}
lab.start(update);
