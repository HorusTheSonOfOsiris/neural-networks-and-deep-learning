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
    if (text !== "") {
      node.textContent = text;
    }
    return node;
  };

  const svgElement = (name, attributes = {}, text = "") => {
    const node = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => {
      node.setAttribute(key, String(value));
    });
    if (text !== "") {
      node.textContent = text;
    }
    return node;
  };

  const sigmoid = (value) => 1 / (1 + Math.exp(-value));
  const sigmoidLike = (value) =>
    sigmoid(value) +
    0.2 * Math.sin(10 * value) * Math.exp(-Math.abs(value));
  const targetFunction = (x) =>
    0.2 +
    0.4 * x * x +
    0.3 * x * Math.sin(15 * x) +
    0.05 * Math.cos(50 * x);
  const inverseTarget = (x) => {
    const value = targetFunction(x);
    return Math.log(value / (1 - value));
  };
  const sample = (fn, count = 400) =>
    Array.from({ length: count + 1 }, (_, index) => {
      const x = index / count;
      return [x, fn(x)];
    });

  const formatTick = (value) => {
    if (Number.isInteger(value)) {
      return String(value);
    }
    return value.toFixed(1);
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
    const titleId = `${id}-final-title`;
    const descriptionId = `${id}-final-description`;
    const clipId = `${id}-final-clip`;
    const svg = svgElement("svg", {
      class: `nndl-universality-plot${editable ? " is-editable" : ""}`,
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      role: "img",
      "aria-labelledby": `${titleId} ${descriptionId}`,
    });

    const definitions = svgElement("defs");
    const clipPath = svgElement("clipPath", { id: clipId });
    clipPath.append(
      svgElement("rect", {
        x: MARGIN.left,
        y: MARGIN.top,
        width: plotWidth,
        height: plotHeight,
      }),
    );
    definitions.append(clipPath);
    svg.append(
      definitions,
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
          formatTick(tick),
        ),
      );
    });

    [0, 0.2, 0.4, 0.6, 0.8, 1].forEach((tick) => {
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
          formatTick(tick),
        ),
      );
    });

    const zeroY = scaleY(Math.max(yDomain[0], Math.min(yDomain[1], 0)));
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
    );

    const curveLayer = svgElement("g", {
      "clip-path": `url(#${clipId})`,
    });
    svg.append(curveLayer);

    const pathData = (points) =>
      points
        .map(([x, y], index) => {
          const visibleY = Math.max(yDomain[0], Math.min(yDomain[1], y));
          return `${index === 0 ? "M" : "L"} ${scaleX(x).toFixed(2)} ${scaleY(
            visibleY,
          ).toFixed(2)}`;
        })
        .join(" ");

    const addCurve = (points, className, attributes = {}) => {
      const path = svgElement("path", {
        class: className,
        d: pathData(points),
        ...attributes,
      });
      curveLayer.append(path);
      return path;
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

    return { svg, addCurve, pathData, eventToData };
  };

  const createControl = ({
    id,
    labelText,
    initial,
    min,
    max,
    step,
    digits,
  }) => {
    const wrapper = element("div", "nndl-parameter-control");
    const header = element("div", "nndl-parameter-header");
    const label = element("label", "nndl-parameter-label", labelText);
    label.htmlFor = id;
    const output = element(
      "output",
      "nndl-parameter-value",
      Number(initial).toFixed(digits),
    );
    output.setAttribute("for", id);
    const range = element("input", "nndl-parameter-range");
    range.id = id;
    range.type = "range";
    range.min = String(min);
    range.max = String(max);
    range.step = String(step);
    range.value = String(initial);
    header.append(label, output);
    wrapper.append(header, range);
    return { wrapper, range, output, digits };
  };

  const createHeader = ({ eyebrow, title, detail, button }) => {
    const header = element("div", "nndl-widget-header");
    const headingGroup = element("div");
    headingGroup.append(
      element("p", "nndl-widget-eyebrow", eyebrow),
      element("p", "nndl-widget-title", title),
      element("p", "nndl-widget-detail", detail),
    );
    header.append(headingGroup);
    if (button) {
      header.append(button);
    }
    return header;
  };

  const randomHeight = () => (Math.round(Math.random() * 30) - 15) / 10;

  const enhanceDesignFunction = () => {
    const container = document.getElementById("design_function");
    if (!container) {
      return;
    }

    const widget = element(
      "section",
      "nndl-universality-widget nndl-design-widget",
    );
    const resetButton = element("button", "nndl-widget-button", "Reset");
    resetButton.type = "button";
    const header = createHeader({
      eyebrow: "Challenge",
      title: "Approximate σ⁻¹(f(x))",
      detail:
        "Adjust the five bin heights with the sliders, or draw directly on the graph.",
      button: resetButton,
    });
    const controlsElement = element("div", "nndl-parameter-grid");
    const controls = Array.from({ length: 5 }, (_, index) => {
      const control = createControl({
        id: `design-function-h${index + 1}`,
        labelText: `Height h${["₁", "₂", "₃", "₄", "₅"][index]}`,
        initial: randomHeight(),
        min: -2.5,
        max: 2.5,
        step: 0.1,
        digits: 1,
      });
      controlsElement.append(control.wrapper);
      return control;
    });
    const plot = createPlot({
      id: "design_function",
      title: "Target and five-bin approximation",
      description:
        "The smooth inverse-sigmoid target is overlaid with an editable five-bin approximation.",
      yDomain: [-2.5, 2.5],
      yTicks: [-2, -1, 0, 1, 2],
      editable: true,
    });
    plot.addCurve(
      sample(inverseTarget),
      "nndl-universality-curve nndl-design-target",
      {
        "aria-hidden": "true",
      },
    );
    const approximation = plot.addCurve(
      [],
      "nndl-universality-curve nndl-design-approximation",
      {
        "aria-hidden": "true",
      },
    );
    const status = element("p", "nndl-universality-status");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");

    const heights = () => controls.map(({ range }) => Number(range.value));
    const approximationPoints = (values) => {
      const points = [[0, values[0]]];
      values.forEach((height, index) => {
        const end = (index + 1) / values.length;
        points.push([end, height]);
        if (index < values.length - 1) {
          points.push([end, values[index + 1]]);
        }
      });
      return points;
    };
    const deviation = (values) =>
      sample((x) => {
        const bin = Math.min(values.length - 1, Math.floor(x * values.length));
        return Math.abs(values[bin] - inverseTarget(x));
      }, 1000).reduce((sum, [, difference]) => sum + difference, 0) / 1001;

    const update = () => {
      controls.forEach(({ range, output, digits }) => {
        const value = Number(range.value).toFixed(digits);
        output.value = value;
        output.textContent = value;
      });
      const values = heights();
      approximation.setAttribute("d", plot.pathData(approximationPoints(values)));
      const averageDeviation = deviation(values);
      const succeeded = averageDeviation <= 0.4;
      widget.classList.toggle("is-success", succeeded);
      status.classList.toggle("is-success", succeeded);
      status.textContent = succeeded
        ? `Average absolute deviation: ${averageDeviation.toFixed(3)} — challenge complete.`
        : `Average absolute deviation: ${averageDeviation.toFixed(3)} — reach 0.400 or below.`;
    };

    controls.forEach(({ range }) => range.addEventListener("input", update));
    resetButton.addEventListener("click", () => {
      controls.forEach(({ range }) => {
        range.value = String(randomHeight());
      });
      update();
      controls[0].range.focus();
    });

    const setHeightFromPointer = (event) => {
      const point = plot.eventToData(event);
      const index = Math.min(4, Math.floor(point.x * 5));
      const control = controls[index];
      const rounded = Math.round(point.y * 10) / 10;
      control.range.value = String(
        Math.max(
          Number(control.range.min),
          Math.min(Number(control.range.max), rounded),
        ),
      );
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

    widget.append(header, controlsElement, plot.svg, status);
    container.replaceChildren(widget);
    container.classList.add("is-enhanced");
    update();
  };

  const enhanceRamping = () => {
    const container = document.getElementById("ramping");
    if (!container) {
      return;
    }

    const widget = element("section", "nndl-universality-widget");
    const header = createHeader({
      eyebrow: "Activation explorer",
      title: "Turn s(wx + b) into a step",
      detail:
        "Increase the weight to contract the activation; change the bias to move its transition.",
    });
    const controlsElement = element("div", "nndl-parameter-grid");
    const weight = createControl({
      id: "ramping-weight",
      labelText: "Weight w",
      initial: 6,
      min: -100,
      max: 100,
      step: 1,
      digits: 0,
    });
    const bias = createControl({
      id: "ramping-bias",
      labelText: "Bias b",
      initial: -3,
      min: -100,
      max: 100,
      step: 1,
      digits: 0,
    });
    controlsElement.append(weight.wrapper, bias.wrapper);
    const plot = createPlot({
      id: "ramping",
      title: "Output s(wx + b)",
      description:
        "The sigmoid-like activation is evaluated from x equals zero to one using the selected weight and bias.",
      yDomain: [-0.15, 1.15],
      yTicks: [0, 0.5, 1],
    });
    const curve = plot.addCurve([], "nndl-universality-curve", {
      "aria-hidden": "true",
    });
    const status = element("p", "nndl-universality-status");
    status.setAttribute("role", "status");

    const update = () => {
      const w = Number(weight.range.value);
      const b = Number(bias.range.value);
      [
        [weight, w],
        [bias, b],
      ].forEach(([control, value]) => {
        const formatted = value.toFixed(control.digits);
        control.output.value = formatted;
        control.output.textContent = formatted;
      });
      curve.setAttribute(
        "d",
        plot.pathData(sample((x) => sigmoidLike(w * x + b), 600)),
      );
      status.textContent =
        Math.abs(w) < 0.0001
          ? "The output is constant when w = 0."
          : `Nominal transition position −b/w = ${(-b / w).toFixed(3)}.`;
    };

    weight.range.addEventListener("input", update);
    bias.range.addEventListener("input", update);
    widget.append(header, controlsElement, plot.svg, status);
    container.replaceChildren(widget);
    container.classList.add("is-enhanced");
    update();
  };

  const smoothBump = (x, start, end, height) =>
    height * (sigmoid(300 * (x - start)) - sigmoid(300 * (x - end)));

  const bumpConfigurations = [
    {
      id: "series_of_bumps",
      title: "Five smooth bump functions",
      description:
        "Five steep sigmoid pairs approximate the inverse-sigmoid target in adjacent intervals.",
      shift: 0,
      heights: [-1.3, -1.8, -0.5, -0.9, 0.3],
      yDomain: [-2, 2],
      yTicks: [-2, -1, 0, 1, 2],
    },
    {
      id: "half_bumps",
      title: "Half-height bump approximation",
      description:
        "The same intervals approximate one half of the inverse-sigmoid target.",
      shift: 0,
      heights: [-0.65, -0.9, -0.25, -0.45, 0.15],
      yDomain: [-2, 2],
      yTicks: [-2, -1, 0, 1, 2],
    },
    {
      id: "shifted_bumps",
      title: "Shifted half-height bumps",
      description:
        "A second half-height approximation shifts every bump by one half-bin.",
      shift: 0.1,
      heights: [-1.55 / 2, -1.15 / 2, -0.7 / 2, -0.6 / 2, 0.3],
      yDomain: [-2, 2],
      yTicks: [-2, -1, 0, 1, 2],
    },
  ];

  const enhanceBumpPlot = (configuration) => {
    const container = document.getElementById(configuration.id);
    if (!container) {
      return;
    }

    const plot = createPlot({
      id: configuration.id,
      title: configuration.title,
      description: configuration.description,
      yDomain: configuration.yDomain,
      yTicks: configuration.yTicks,
    });
    configuration.heights.forEach((height, index) => {
      const start = index / 5 + configuration.shift;
      const end = (index + 1) / 5 + configuration.shift;
      const bump = (x) => smoothBump(x, start, end, height);
      plot.addCurve(
        sample(bump, 600),
        `nndl-universality-curve nndl-bump-component is-component-${index + 1}`,
        {
          "aria-hidden": "true",
        },
      );
    });

    const note = element(
      "p",
      "nndl-universality-status nndl-bump-legend",
      configuration.shift === 0
        ? "Five sigmoid pairs form smooth bumps on adjacent intervals."
        : "These half-height bumps are shifted by 0.10, moving their narrow transition windows.",
    );
    container.replaceChildren(plot.svg, note);
    container.classList.add("is-enhanced");
  };

  const render = () => {
    enhanceDesignFunction();
    enhanceRamping();
    bumpConfigurations.forEach(enhanceBumpPlot);
  };

  if (window.NNDLPlots) {
    window.NNDLPlots.onReady(render);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, { once: true });
  } else {
    render();
  }
})();
