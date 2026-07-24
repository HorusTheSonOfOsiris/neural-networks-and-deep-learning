(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 680;
  const HEIGHT = 340;
  const MARGIN = { top: 46, right: 24, bottom: 52, left: 66 };

  const element = (name, className = "", text = "") => {
    const node = document.createElement(name);
    if (className) {
      node.className = className;
    }
    if (text) {
      node.textContent = text;
    }
    return node;
  };

  const svgElement = (name, attributes = {}, text = "") => {
    const node = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => {
      node.setAttribute(key, String(value));
    });
    if (text) {
      node.textContent = text;
    }
    return node;
  };

  const sigmoid = (value) => 1 / (1 + Math.exp(-value));
  const sample = (fn, count = 300) =>
    Array.from({ length: count + 1 }, (_, index) => {
      const x = index / count;
      return [x, fn(x)];
    });

  const stepPoints = (steps) => {
    const sorted = [...steps].sort((left, right) => left.s - right.s);
    let value = sorted
      .filter(({ s }) => s < 0)
      .reduce((sum, { weight }) => sum + weight, 0);
    const points = [[0, value]];

    sorted.forEach(({ s, weight }) => {
      if (s < 0 || s > 1) {
        return;
      }
      points.push([s, value]);
      value += weight;
      points.push([s, value]);
    });
    points.push([1, value]);
    return points;
  };

  const createPlot = ({
    id,
    title,
    description,
    yDomain,
    yTicks,
    editable = false,
  }) => {
    const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
    const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
    const scaleX = (x) => MARGIN.left + x * plotWidth;
    const scaleY = (y) =>
      MARGIN.top +
      (1 - (y - yDomain[0]) / (yDomain[1] - yDomain[0])) * plotHeight;
    const titleId = `${id}-plot-title`;
    const descriptionId = `${id}-plot-description`;
    const svg = svgElement("svg", {
      class: `nndl-universality-plot${editable ? " is-editable" : ""}`,
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      role: "img",
      "aria-labelledby": `${titleId} ${descriptionId}`,
    });
    const curve = svgElement("path", {
      class: "nndl-universality-curve",
      d: "",
    });

    svg.append(
      svgElement("title", { id: titleId }, title),
      svgElement("desc", { id: descriptionId }, description),
      svgElement(
        "text",
        {
          class: "nndl-universality-plot-title",
          x: WIDTH / 2,
          y: 26,
          "text-anchor": "middle",
        },
        title,
      ),
    );

    yTicks.forEach((tick) => {
      const y = scaleY(tick);
      svg.append(
        svgElement("line", {
          class: "nndl-universality-gridline",
          x1: MARGIN.left,
          x2: WIDTH - MARGIN.right,
          y1: y,
          y2: y,
          "aria-hidden": "true",
        }),
        svgElement(
          "text",
          {
            class: "nndl-universality-tick",
            x: MARGIN.left - 12,
            y: y + 4,
            "text-anchor": "end",
          },
          Number.isInteger(tick) ? String(tick) : tick.toFixed(1),
        ),
      );
    });

    [0, 0.25, 0.5, 0.75, 1].forEach((tick) => {
      const x = scaleX(tick);
      svg.append(
        svgElement("line", {
          class: "nndl-universality-gridline",
          x1: x,
          x2: x,
          y1: MARGIN.top,
          y2: HEIGHT - MARGIN.bottom,
          "aria-hidden": "true",
        }),
        svgElement(
          "text",
          {
            class: "nndl-universality-tick",
            x,
            y: HEIGHT - 26,
            "text-anchor": "middle",
          },
          tick.toFixed(tick === 0 || tick === 1 ? 0 : 2),
        ),
      );
    });

    const zeroY =
      yDomain[0] <= 0 && yDomain[1] >= 0
        ? scaleY(0)
        : HEIGHT - MARGIN.bottom;
    svg.append(
      svgElement("line", {
        class: "nndl-universality-axis",
        x1: MARGIN.left,
        x2: MARGIN.left,
        y1: MARGIN.top,
        y2: HEIGHT - MARGIN.bottom,
        "aria-hidden": "true",
      }),
      svgElement("line", {
        class: "nndl-universality-axis",
        x1: MARGIN.left,
        x2: WIDTH - MARGIN.right,
        y1: zeroY,
        y2: zeroY,
        "aria-hidden": "true",
      }),
      svgElement(
        "text",
        {
          class: "nndl-universality-label",
          x: WIDTH / 2,
          y: HEIGHT - 5,
          "text-anchor": "middle",
        },
        "x",
      ),
      curve,
    );

    const update = (points) => {
      curve.setAttribute(
        "d",
        points
          .map(
            ([x, y], index) =>
              `${index === 0 ? "M" : "L"} ${scaleX(x).toFixed(2)} ${scaleY(
                Math.max(yDomain[0], Math.min(yDomain[1], y)),
              ).toFixed(2)}`,
          )
          .join(" "),
      );
    };

    const eventToData = (event) => {
      const bounds = svg.getBoundingClientRect();
      const svgX = ((event.clientX - bounds.left) / bounds.width) * WIDTH;
      const svgY = ((event.clientY - bounds.top) / bounds.height) * HEIGHT;
      return {
        x: Math.max(0, Math.min(1, (svgX - MARGIN.left) / plotWidth)),
        y:
          yDomain[1] -
          Math.max(0, Math.min(1, (svgY - MARGIN.top) / plotHeight)) *
            (yDomain[1] - yDomain[0]),
      };
    };

    return { svg, update, eventToData };
  };

  const createControl = (widgetId, definition) => {
    const wrapper = element("div", "nndl-parameter-control");
    const header = element("div", "nndl-parameter-header");
    const inputId = `${widgetId}-${definition.key}`;
    const label = element("label", "nndl-parameter-label", definition.label);
    label.htmlFor = inputId;
    const output = element(
      "output",
      "nndl-parameter-value",
      definition.initial.toFixed(definition.digits),
    );
    output.setAttribute("for", inputId);

    const range = element("input", "nndl-parameter-range");
    range.id = inputId;
    range.type = "range";
    range.min = String(definition.min);
    range.max = String(definition.max);
    range.step = String(definition.step);
    range.value = String(definition.initial);
    header.append(label, output);
    wrapper.append(header, range);
    return { wrapper, range, output, definition };
  };

  const configurations = [
    {
      id: "basic_manipulation",
      title: "Shape a sigmoid neuron",
      detail: "Change the weight and bias in a = σ(wx + b).",
      plotTitle: "Output from top hidden neuron",
      yDomain: [0, 1],
      yTicks: [0, 0.5, 1],
      controls: [
        { key: "w", label: "Weight w", initial: 8, min: -200, max: 200, step: 1, digits: 0 },
        { key: "b", label: "Bias b", initial: -4, min: -200, max: 200, step: 1, digits: 0 },
      ],
      points: ({ w, b }) => sample((x) => sigmoid(w * x + b)),
      status: ({ w, b }) => `a(x) = σ(${w.toFixed(0)}x ${b < 0 ? "−" : "+"} ${Math.abs(b).toFixed(0)})`,
    },
    {
      id: "step",
      title: "Locate the sigmoid step",
      detail: "The steep transition occurs at s = −b/w.",
      plotTitle: "Output from top hidden neuron",
      yDomain: [0, 1],
      yTicks: [0, 0.5, 1],
      controls: [
        { key: "w", label: "Weight w", initial: 100, min: -200, max: 200, step: 1, digits: 0 },
        { key: "b", label: "Bias b", initial: -40, min: -200, max: 200, step: 1, digits: 0 },
      ],
      points: ({ w, b }) => sample((x) => sigmoid(w * x + b)),
      status: ({ w, b }) =>
        Math.abs(w) < 0.0001
          ? "Step position is undefined when w = 0."
          : `Step position s = −b/w = ${(-b / w).toFixed(2)}`,
    },
    {
      id: "step_parameterization",
      title: "Move a step directly",
      detail: "The parameter s replaces the corresponding weight and bias.",
      plotTitle: "Output from top hidden neuron",
      yDomain: [0, 1],
      yTicks: [0, 0.5, 1],
      controls: [
        { key: "s", label: "Step position s", initial: 0.4, min: -0.25, max: 1.25, step: 0.01, digits: 2 },
      ],
      points: ({ s }) => stepPoints([{ s, weight: 1 }]),
      status: ({ s }) => `The neuron turns on at x = ${s.toFixed(2)}.`,
    },
    {
      id: "two_hn_network",
      title: "Combine two hidden neurons",
      detail: "Adjust both step positions and their output weights.",
      plotTitle: "Weighted output from hidden layer",
      yDomain: [-4, 4],
      yTicks: [-4, -2, 0, 2, 4],
      controls: [
        { key: "s1", label: "Step s₁", initial: 0.4, min: -0.25, max: 1.25, step: 0.01, digits: 2 },
        { key: "s2", label: "Step s₂", initial: 0.6, min: -0.25, max: 1.25, step: 0.01, digits: 2 },
        { key: "w1", label: "Weight w₁", initial: 0.6, min: -3, max: 3, step: 0.1, digits: 1 },
        { key: "w2", label: "Weight w₂", initial: 1.2, min: -3, max: 3, step: 0.1, digits: 1 },
      ],
      points: ({ s1, s2, w1, w2 }) =>
        stepPoints([
          { s: s1, weight: w1 },
          { s: s2, weight: w2 },
        ]),
      status: ({ w1, w2 }) =>
        `Weighted output = ${w1.toFixed(1)}a₁ ${w2 < 0 ? "−" : "+"} ${Math.abs(w2).toFixed(1)}a₂`,
    },
    {
      id: "bump_fn",
      title: "Build one bump",
      detail: "Two opposed step functions form a bump of height h.",
      plotTitle: "Weighted output from hidden layer",
      yDomain: [-2, 2],
      yTicks: [-2, -1, 0, 1, 2],
      controls: [
        { key: "s1", label: "Start s₁", initial: 0.4, min: -0.25, max: 1.25, step: 0.01, digits: 2 },
        { key: "s2", label: "End s₂", initial: 0.6, min: -0.25, max: 1.25, step: 0.01, digits: 2 },
        { key: "h", label: "Height h", initial: 0.6, min: -2, max: 2, step: 0.1, digits: 1 },
      ],
      points: ({ s1, s2, h }) =>
        stepPoints([
          { s: s1, weight: h },
          { s: s2, weight: -h },
        ]),
      status: ({ s1, s2, h }) =>
        `Height ${h.toFixed(1)} between x = ${Math.min(s1, s2).toFixed(2)} and ${Math.max(s1, s2).toFixed(2)}.`,
    },
    {
      id: "double_bump",
      title: "Combine two bumps",
      detail: "Each pair of step neurons controls one interval.",
      plotTitle: "Weighted output from hidden layer",
      yDomain: [-4, 4],
      yTicks: [-4, -2, 0, 2, 4],
      controls: [
        { key: "s1", label: "Start s₁", initial: 0.4, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "s2", label: "End s₂", initial: 0.6, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "h1", label: "Height h₁", initial: -1.2, min: -3, max: 3, step: 0.1, digits: 1 },
        { key: "s3", label: "Start s₃", initial: 0.7, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "s4", label: "End s₄", initial: 0.9, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "h2", label: "Height h₂", initial: 0.3, min: -3, max: 3, step: 0.1, digits: 1 },
      ],
      points: ({ s1, s2, h1, s3, s4, h2 }) =>
        stepPoints([
          { s: s1, weight: h1 },
          { s: s2, weight: -h1 },
          { s: s3, weight: h2 },
          { s: s4, weight: -h2 },
        ]),
      status: ({ h1, h2 }) =>
        `Bump heights: h₁ = ${h1.toFixed(1)}, h₂ = ${h2.toFixed(1)}.`,
    },
    {
      id: "five_bumps",
      title: "Draw a five-bin function",
      detail: "Use the five heights, or drag directly on the graph.",
      plotTitle: "Weighted output from hidden layer",
      yDomain: [-2, 2],
      yTicks: [-2, -1, 0, 1, 2],
      editable: true,
      controls: Array.from({ length: 5 }, (_, index) => ({
        key: `h${index + 1}`,
        label: `Height h${["₁", "₂", "₃", "₄", "₅"][index]}`,
        initial: (Math.round(Math.random() * 30) - 15) / 10,
        min: -2,
        max: 2,
        step: 0.1,
        digits: 1,
      })),
      points: (values) =>
        stepPoints(
          Array.from({ length: 5 }, (_, index) => [
            { s: index / 5, weight: values[`h${index + 1}`] },
            { s: (index + 1) / 5, weight: -values[`h${index + 1}`] },
          ]).flat(),
        ),
      status: () => "Five pairs of hidden neurons create five independently adjustable bins.",
    },
  ];

  const enhance = (configuration) => {
    const container = document.getElementById(configuration.id);
    if (!container) {
      return;
    }

    const widget = element("section", "nndl-universality-widget");
    const header = element("div", "nndl-widget-header");
    const headingGroup = element("div");
    const eyebrow = element(
      "p",
      "nndl-widget-eyebrow",
      "Universal approximation",
    );
    const heading = element("p", "nndl-widget-title", configuration.title);
    const detail = element("p", "nndl-widget-detail", configuration.detail);
    headingGroup.append(eyebrow, heading, detail);
    header.append(headingGroup);

    const controlsElement = element("div", "nndl-parameter-grid");
    const controls = configuration.controls.map((definition) => {
      const control = createControl(configuration.id, definition);
      controlsElement.append(control.wrapper);
      return control;
    });
    const plot = createPlot({
      id: configuration.id,
      title: configuration.plotTitle,
      description: configuration.detail,
      yDomain: configuration.yDomain,
      yTicks: configuration.yTicks,
      editable: configuration.editable,
    });
    const status = element("p", "nndl-universality-status");
    status.setAttribute("role", "status");

    const values = () =>
      Object.fromEntries(
        controls.map(({ definition, range }) => [
          definition.key,
          Number(range.value),
        ]),
      );
    const update = () => {
      controls.forEach(({ definition, range, output }) => {
        const formatted = Number(range.value).toFixed(definition.digits);
        output.value = formatted;
        output.textContent = formatted;
      });
      const currentValues = values();
      plot.update(configuration.points(currentValues));
      status.textContent = configuration.status(currentValues);
    };

    controls.forEach(({ range }) => range.addEventListener("input", update));

    if (configuration.editable) {
      const setHeightFromPointer = (event) => {
        const point = plot.eventToData(event);
        const bin = Math.min(4, Math.floor(point.x * 5));
        const control = controls[bin];
        const clamped = Math.max(
          Number(control.range.min),
          Math.min(Number(control.range.max), point.y),
        );
        control.range.value = String(Math.round(clamped * 10) / 10);
        update();
      };
      plot.svg.addEventListener("pointerdown", (event) => {
        plot.svg.setPointerCapture(event.pointerId);
        setHeightFromPointer(event);
      });
      plot.svg.addEventListener("pointermove", (event) => {
        if (plot.svg.hasPointerCapture(event.pointerId)) {
          setHeightFromPointer(event);
        }
      });
    }

    widget.append(header, controlsElement, plot.svg, status);
    container.replaceChildren(widget);
    container.classList.add("is-enhanced");
    update();
  };

  const render = () => configurations.forEach(enhance);
  if (window.NNDLPlots) {
    window.NNDLPlots.onReady(render);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, { once: true });
  } else {
    render();
  }
})();
