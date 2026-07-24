(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 640;
  const HEIGHT = 360;
  const MARGIN = { top: 56, right: 28, bottom: 58, left: 68 };

  const plots = [
    {
      id: "sigmoid_graph",
      title: "Sigmoid function",
      description:
        "The sigmoid function rises smoothly from zero to one as z increases.",
      points: Array.from({ length: 201 }, (_, index) => {
        const x = -5 + (10 * index) / 200;
        return [x, 1 / (1 + Math.exp(-x))];
      }),
    },
    {
      id: "step_graph",
      title: "Step function",
      description:
        "The step function is zero below z equals zero and one from z equals zero onward.",
      points: [
        [-5, 0],
        [0, 0],
        [0, 1],
        [5, 1],
      ],
    },
  ];

  const createSvgElement = (name, attributes = {}, text = "") => {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key, String(value));
    });
    if (text) {
      element.textContent = text;
    }
    return element;
  };

  const drawPlot = ({
    id,
    title,
    description,
    points,
    xDomain = [-5, 5],
    yDomain = [0, 1],
    xTicks = [-4, -3, -2, -1, 0, 1, 2, 3, 4],
    yTicks = [0, 0.2, 0.4, 0.6, 0.8, 1],
    xLabel = "z",
    yLabel = "",
    xAxisAt = yDomain[0],
    yAxisAt = xDomain[0],
    scatterPoints = [],
    yTickFormat = (value) => value.toFixed(1),
  }) => {
    const container = document.getElementById(id);
    if (!container) {
      return;
    }

    const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
    const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
    const scaleX = (value) =>
      MARGIN.left +
      ((value - xDomain[0]) / (xDomain[1] - xDomain[0])) * plotWidth;
    const scaleY = (value) =>
      MARGIN.top +
      (1 - (value - yDomain[0]) / (yDomain[1] - yDomain[0])) *
        plotHeight;
    const xAxisY = scaleY(xAxisAt);
    const yAxisX = scaleX(yAxisAt);
    const titleId = `${id}-title`;
    const descriptionId = `${id}-description`;
    const svg = createSvgElement("svg", {
      class: "nndl-plot",
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      role: "img",
      "aria-labelledby": `${titleId} ${descriptionId}`,
    });

    svg.append(
      createSvgElement("title", { id: titleId }, title),
      createSvgElement("desc", { id: descriptionId }, description),
      createSvgElement(
        "text",
        {
          class: "nndl-plot-title",
          x: WIDTH / 2,
          y: 30,
          "text-anchor": "middle",
        },
        title,
      ),
    );

    const grid = createSvgElement("g", { "aria-hidden": "true" });
    yTicks.forEach((value) => {
      const y = scaleY(value);
      grid.append(
        createSvgElement("line", {
          class: "nndl-plot-gridline",
          x1: MARGIN.left,
          x2: WIDTH - MARGIN.right,
          y1: y,
          y2: y,
        }),
        createSvgElement(
          "text",
          {
            class: "nndl-plot-tick",
            x: yAxisX - 12,
            y: y + 4,
            "text-anchor": "end",
          },
          yTickFormat(value),
        ),
      );
    });

    xTicks.forEach((value) => {
      const x = scaleX(value);
      grid.append(
        createSvgElement("line", {
          class: "nndl-plot-gridline",
          x1: x,
          x2: x,
          y1: MARGIN.top,
          y2: HEIGHT - MARGIN.bottom,
        }),
        createSvgElement(
          "text",
          {
            class: "nndl-plot-tick",
            x,
            y: xAxisY + 25,
            "text-anchor": "middle",
          },
          value,
        ),
      );
    });
    svg.append(grid);

    svg.append(
      createSvgElement("line", {
        class: "nndl-plot-axis",
        x1: yAxisX,
        x2: yAxisX,
        y1: MARGIN.top,
        y2: HEIGHT - MARGIN.bottom,
        "aria-hidden": "true",
      }),
      createSvgElement("line", {
        class: "nndl-plot-axis",
        x1: MARGIN.left,
        x2: WIDTH - MARGIN.right,
        y1: xAxisY,
        y2: xAxisY,
        "aria-hidden": "true",
      }),
      createSvgElement(
        "text",
        {
          class: "nndl-plot-label",
          x: MARGIN.left + plotWidth / 2,
          y: HEIGHT - 12,
          "text-anchor": "middle",
        },
        xLabel,
      ),
    );

    if (yLabel) {
      svg.append(
        createSvgElement(
          "text",
          {
            class: "nndl-plot-label",
            x: 20,
            y: MARGIN.top + plotHeight / 2,
            "text-anchor": "middle",
            transform: `rotate(-90 20 ${MARGIN.top + plotHeight / 2})`,
          },
          yLabel,
        ),
      );
    }

    if (points.length > 0) {
      const pathData = points
        .map(
          ([x, y], index) =>
            `${index === 0 ? "M" : "L"} ${scaleX(x).toFixed(2)} ${scaleY(y).toFixed(2)}`,
        )
        .join(" ");
      svg.append(
        createSvgElement("path", {
          class: "nndl-plot-curve",
          d: pathData,
        }),
      );
    }

    scatterPoints.forEach(([x, y]) => {
      svg.append(
        createSvgElement("circle", {
          class: "nndl-plot-point",
          cx: scaleX(x),
          cy: scaleY(y),
          r: 5,
        }),
      );
    });

    container.replaceChildren(svg);
    container.classList.add("is-enhanced");
  };

  const onReady = (callback) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  };

  window.NNDLPlots = { drawPlot, onReady };

  const render = () => plots.forEach(drawPlot);
  onReady(render);
})();
