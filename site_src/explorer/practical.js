import {$, experiment, fitLine, measureTable, onRedraw, plot, seededRandom} from "./core.js";

// Each instrument supplies raw readings, linearised coordinates and the
// conversion from the fitted coefficients to its physical constants.
export function practical({id, question, steps, control, reading, xLabel, yLabel,
                          observe, point, constants, throughOrigin = false}) {
  const lab = experiment(id, question, steps);
  const setting = lab.range("setting", ...control);
  const panel = $(id), canvas = $(id+"-plot");
  const table = measureTable({columns:[control[0]+" ("+control[5]+")", reading, xLabel, yLabel]});
  panel.querySelector(".experiment-figures").append(table.element);
  const outputs = constants.map(({key,label}) => lab.result(key,label));
  const actions = document.createElement("div");
  function button(label, fn) {
    const b = document.createElement("button");
    b.textContent = label;
    b.type = "button";
    b.addEventListener("click", fn);
    actions.append(b);
  }
  const points = [];
  let random = seededRandom(418), fit;
  function draw() {
    const series = points.map(p => ({points:[p]}));
    if (fit) {
      const xs = points.map(([x]) => x);
      const ends = [throughOrigin ? 0 : Math.min(...xs), Math.max(...xs)];
      series.unshift({points:ends.map(x => [x, fit.gradient*x+fit.intercept])});
    }
    plot(canvas,{xLabel,yLabel,series});
  }
  function updateFit() {
    const xs = points.map(([x]) => x), ys = points.map(([,y]) => y);
    fit = points.length >= 3 && new Set(xs).size >= 2 ? fitLine(xs,ys,{throughOrigin}) : null;
    constants.forEach(({unit,estimate},i) => {
      if (!fit) { outputs[i]("Record at least three readings at different settings"); return; }
      const [value,error] = estimate(fit);
      if (!Number.isFinite(value) || !Number.isFinite(error)) {
        outputs[i]("Record a wider range of settings");
        return;
      }
      const percent = value ? (100*error/Math.abs(value)).toPrecision(3)+"%" : "undefined";
      outputs[i](value.toPrecision(6)+" ± "+error.toPrecision(3)+" "+unit+" ("+percent+")");
    });
    draw();
  }
  button("Record",() => {
    const x = setting(), raw = observe(x,2*random()-1), coords = point(x,raw);
    points.push(coords);
    table.addRow([x,raw,...coords].map(v => Number(v.toPrecision(7))));
    updateFit();
  });
  button("Clear",() => {
    table.clear();
    points.length = 0;
    random = seededRandom(418);
    updateFit();
  });
  panel.querySelector(".controls").append(actions);
  updateFit();
  onRedraw(draw);
}
