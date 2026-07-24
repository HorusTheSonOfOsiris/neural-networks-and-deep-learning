(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 680;
  const HEIGHT = 430;
  const RESOLUTION = 20;

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
  const steepStep = (value, step) => sigmoid(1000 * (value - step));
  const bump = (value, start, end) =>
    steepStep(value, start) - steepStep(value, end);

  const configurations = [
    {
      id: "ti_graph",
      title: "A step surface in x",
      detail: "The y input has weight zero, so every y slice is identical.",
      domain: [0, 1],
      controls: [
        { key: "w1", label: "Weight w₁", initial: 8, min: -100, max: 100, step: 1, digits: 0 },
        { key: "b", label: "Bias b", initial: -5, min: -100, max: 100, step: 1, digits: 0 },
      ],
      fn: ({ w1, b }, x) => sigmoid(w1 * x + b),
      status: ({ w1, b }) =>
        Math.abs(w1) < 0.001
          ? "The output is constant when w₁ = 0."
          : `The x transition is near ${(-b / w1).toFixed(2)}; w₂ = 0.`,
    },
    {
      id: "ti_graph_redux",
      title: "Move the x step",
      detail: "Parameterize the sharp transition directly by its x position.",
      domain: [0, 1],
      controls: [
        { key: "s", label: "x step sₓ", initial: 0.5, min: 0, max: 1, step: 0.01, digits: 2 },
      ],
      fn: ({ s }, x) => steepStep(x, s),
      status: ({ s }) => `Output switches on when x crosses ${s.toFixed(2)}.`,
    },
    {
      id: "y_step",
      title: "Move the y step",
      detail: "Now the x input has weight zero and the transition runs along y.",
      domain: [0, 1],
      controls: [
        { key: "s", label: "y step sᵧ", initial: 0.5, min: 0, max: 1, step: 0.01, digits: 2 },
      ],
      fn: ({ s }, _x, y) => steepStep(y, s),
      status: ({ s }) => `Output switches on when y crosses ${s.toFixed(2)}.`,
    },
    {
      id: "bump_3d",
      title: "An x-direction bump",
      detail: "Two opposed x steps form a ridge whose height is h.",
      domain: [-2, 2],
      controls: [
        { key: "s1", label: "Start s₁", initial: 0.3, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "s2", label: "End s₂", initial: 0.7, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "h", label: "Height h", initial: 0.6, min: -2, max: 2, step: 0.1, digits: 1 },
      ],
      fn: ({ s1, s2, h }, x) => h * bump(x, s1, s2),
      status: ({ s1, s2, h }) =>
        `x ridge from ${s1.toFixed(2)} to ${s2.toFixed(2)}, height ${h.toFixed(1)}.`,
    },
    {
      id: "bump_3d_y",
      title: "A y-direction bump",
      detail: "The same construction, rotated to use the y input.",
      domain: [-2, 2],
      controls: [
        { key: "s1", label: "Start s₁", initial: 0.3, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "s2", label: "End s₂", initial: 0.7, min: 0, max: 1, step: 0.01, digits: 2 },
        { key: "h", label: "Height h", initial: 0.6, min: -2, max: 2, step: 0.1, digits: 1 },
      ],
      fn: ({ s1, s2, h }, _x, y) => h * bump(y, s1, s2),
      status: ({ s1, s2, h }) =>
        `y ridge from ${s1.toFixed(2)} to ${s2.toFixed(2)}, height ${h.toFixed(1)}.`,
    },
    {
      id: "xy_bump",
      title: "Add x and y bumps",
      detail: "Overlapping ridges add; their intersection reaches twice the height.",
      domain: [-4, 4],
      controls: [
        { key: "h", label: "Ridge height h", initial: 0.3, min: -2, max: 2, step: 0.1, digits: 1 },
      ],
      fn: ({ h }, x, y) =>
        h * bump(x, 0.4, 0.6) + h * bump(y, 0.3, 0.7),
      status: ({ h }) =>
        `Each ridge has height ${h.toFixed(1)}; the overlap reaches ${(2 * h).toFixed(1)}.`,
    },
    {
      id: "tower_construction",
      title: "Turn the overlap into a tower",
      detail: "The output sigmoid selects the region where both ridges overlap.",
      domain: [0, 1],
      controls: [
        { key: "h", label: "Input weight h", initial: 0.3, min: -20, max: 20, step: 0.1, digits: 1 },
        { key: "b", label: "Output bias b", initial: -0.5, min: -30, max: 30, step: 0.1, digits: 1 },
      ],
      fn: ({ h, b }, x, y) =>
        sigmoid(
          b + h * bump(x, 0.4, 0.6) + h * bump(y, 0.3, 0.7),
        ),
      status: ({ h, b }) =>
        `Output = σ(${h.toFixed(1)}·x-bump + ${h.toFixed(1)}·y-bump ${b < 0 ? "−" : "+"} ${Math.abs(b).toFixed(1)}).`,
    },
    {
      id: "the_two_towers",
      title: "Weight two tower functions",
      detail: "Two small regions contribute independently to the weighted output.",
      domain: [-2, 2],
      controls: [
        { key: "w1", label: "Tower weight w₁", initial: 0.7, min: -2, max: 2, step: 0.1, digits: 1 },
        { key: "w2", label: "Tower weight w₂", initial: 0.5, min: -2, max: 2, step: 0.1, digits: 1 },
      ],
      fn: ({ w1, w2 }, x, y) =>
        w1 * (x >= 0.1 && x <= 0.2 && y >= 0.8 && y <= 0.9 ? 1 : 0) +
        w2 * (x >= 0.7 && x <= 0.8 && y >= 0.2 && y <= 0.3 ? 1 : 0),
      status: ({ w1, w2 }) =>
        `Tower heights are ${w1.toFixed(1)} and ${w2.toFixed(1)}.`,
    },
  ];

  const createControl = (widgetId, definition) => {
    const wrapper = element("div", "nndl-parameter-control");
    const header = element("div", "nndl-parameter-header");
    const id = `${widgetId}-${definition.key}`;
    const label = element("label", "nndl-parameter-label", definition.label);
    label.htmlFor = id;
    const output = element(
      "output",
      "nndl-parameter-value",
      definition.initial.toFixed(definition.digits),
    );
    output.setAttribute("for", id);
    const range = element("input", "nndl-parameter-range");
    range.id = id;
    range.type = "range";
    range.min = String(definition.min);
    range.max = String(definition.max);
    range.step = String(definition.step);
    range.value = String(definition.initial);
    header.append(label, output);
    wrapper.append(header, range);
    return { wrapper, range, output, definition };
  };

  const createSurface = (id, title, detail, domain) => {
    const titleId = `${id}-surface-title`;
    const descriptionId = `${id}-surface-description`;
    const svg = svgElement("svg", {
      class: "nndl-surface",
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      role: "img",
      "aria-labelledby": `${titleId} ${descriptionId}`,
    });
    const surfaceGroup = svgElement("g", {
      class: "nndl-surface-cells",
      "aria-hidden": "true",
    });

    const project = (x, y, normalizedZ) => [
      WIDTH / 2 + (x - y) * 245,
      392 - (x + y) * 90 - normalizedZ * 155,
    ];
    const pointString = (point) =>
      `${point[0].toFixed(2)},${point[1].toFixed(2)}`;
    const zeroPlane = Math.max(
      0,
      Math.min(1, (0 - domain[0]) / (domain[1] - domain[0])),
    );
    const base = [
      project(0, 0, zeroPlane),
      project(1, 0, zeroPlane),
      project(1, 1, zeroPlane),
      project(0, 1, zeroPlane),
    ];

    svg.append(
      svgElement("title", { id: titleId }, title),
      svgElement("desc", { id: descriptionId }, detail),
      svgElement(
        "text",
        {
          class: "nndl-universality-plot-title",
          x: WIDTH / 2,
          y: 28,
          "text-anchor": "middle",
        },
        "Output surface",
      ),
      svgElement("polygon", {
        class: "nndl-surface-base",
        points: base.map(pointString).join(" "),
      }),
      surfaceGroup,
    );

    const origin = project(0, 0, zeroPlane);
    const xEnd = project(1.12, 0, zeroPlane);
    const yEnd = project(0, 1.12, zeroPlane);
    const zEnd = project(0, 0, 1.05);
    [
      [origin, xEnd, "x", 12, 5],
      [origin, yEnd, "y", -12, 5],
      [origin, zEnd, "output", 0, -8],
    ].forEach(([start, end, label, dx, dy]) => {
      svg.append(
        svgElement("line", {
          class: "nndl-surface-axis",
          x1: start[0],
          y1: start[1],
          x2: end[0],
          y2: end[1],
          "aria-hidden": "true",
        }),
        svgElement(
          "text",
          {
            class: "nndl-surface-label",
            x: end[0] + dx,
            y: end[1] + dy,
            "text-anchor": "middle",
          },
          label,
        ),
      );
    });

    const update = (fn) => {
      const cells = [];
      for (let row = 0; row < RESOLUTION; row += 1) {
        for (let column = 0; column < RESOLUTION; column += 1) {
          const x0 = column / RESOLUTION;
          const x1 = (column + 1) / RESOLUTION;
          const y0 = row / RESOLUTION;
          const y1 = (row + 1) / RESOLUTION;
          const values = [
            fn(x0, y0),
            fn(x1, y0),
            fn(x1, y1),
            fn(x0, y1),
          ].map((value) => Math.max(domain[0], Math.min(domain[1], value)));
          const normalized = values.map(
            (value) => (value - domain[0]) / (domain[1] - domain[0]),
          );
          cells.push({
            depth: x0 + y0,
            average: values.reduce((sum, value) => sum + value, 0) / 4,
            normalized:
              normalized.reduce((sum, value) => sum + value, 0) / 4,
            points: [
              project(x0, y0, normalized[0]),
              project(x1, y0, normalized[1]),
              project(x1, y1, normalized[2]),
              project(x0, y1, normalized[3]),
            ],
          });
        }
      }
      cells.sort((left, right) => right.depth - left.depth);
      const fragment = document.createDocumentFragment();
      cells.forEach((cell) => {
        fragment.append(
          svgElement("polygon", {
            class:
              cell.average < 0
                ? "nndl-surface-cell is-negative"
                : "nndl-surface-cell",
            points: cell.points.map(pointString).join(" "),
            "fill-opacity": (0.2 + 0.72 * cell.normalized).toFixed(3),
          }),
        );
      });
      surfaceGroup.replaceChildren(fragment);
    };

    return { svg, update };
  };

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
      "Two-input construction",
    );
    const heading = element("p", "nndl-widget-title", configuration.title);
    const detail = element("p", "nndl-widget-detail", configuration.detail);
    headingGroup.append(eyebrow, heading, detail);
    header.append(headingGroup);

    const controlGrid = element("div", "nndl-parameter-grid");
    const controls = configuration.controls.map((definition) => {
      const control = createControl(configuration.id, definition);
      controlGrid.append(control.wrapper);
      return control;
    });
    const surface = createSurface(
      configuration.id,
      configuration.title,
      configuration.detail,
      configuration.domain,
    );
    const status = element("p", "nndl-universality-status");
    status.setAttribute("role", "status");

    const currentValues = () =>
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
      const values = currentValues();
      surface.update((x, y) => configuration.fn(values, x, y));
      status.textContent = configuration.status(values);
    };

    controls.forEach(({ range }) => range.addEventListener("input", update));
    widget.append(header, controlGrid, surface.svg, status);
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
