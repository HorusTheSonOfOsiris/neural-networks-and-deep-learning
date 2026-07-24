(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 640;
  const HEIGHT = 360;
  const MARGIN = { top: 56, right: 28, bottom: 58, left: 68 };
  const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right;
  const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom;

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

  const scaleX = (value) => MARGIN.left + ((value + 5) / 10) * PLOT_WIDTH;
  const scaleY = (value) => MARGIN.top + (1 - value) * PLOT_HEIGHT;

  const drawPlot = ({ id, title, description, points }) => {
    const container = document.getElementById(id);
    if (!container) {
      return;
    }

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
    for (let index = 0; index <= 5; index += 1) {
      const value = index / 5;
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
            x: MARGIN.left - 12,
            y: y + 4,
            "text-anchor": "end",
          },
          value.toFixed(1),
        ),
      );
    }

    for (let value = -4; value <= 4; value += 1) {
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
            y: HEIGHT - MARGIN.bottom + 25,
            "text-anchor": "middle",
          },
          value,
        ),
      );
    }
    svg.append(grid);

    svg.append(
      createSvgElement("line", {
        class: "nndl-plot-axis",
        x1: MARGIN.left,
        x2: MARGIN.left,
        y1: MARGIN.top,
        y2: HEIGHT - MARGIN.bottom,
        "aria-hidden": "true",
      }),
      createSvgElement("line", {
        class: "nndl-plot-axis",
        x1: MARGIN.left,
        x2: WIDTH - MARGIN.right,
        y1: HEIGHT - MARGIN.bottom,
        y2: HEIGHT - MARGIN.bottom,
        "aria-hidden": "true",
      }),
      createSvgElement(
        "text",
        {
          class: "nndl-plot-label",
          x: MARGIN.left + PLOT_WIDTH / 2,
          y: HEIGHT - 12,
          "text-anchor": "middle",
        },
        "z",
      ),
    );

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

    container.replaceChildren(svg);
    container.classList.add("is-enhanced");
  };

  const render = () => plots.forEach(drawPlot);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, { once: true });
  } else {
    render();
  }
})();
