(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const gradientValues = [
    [
      -0.003970677333144113,
      -0.0031684316985881185,
      0.008103235909196014,
      0.012598010584130365,
      -0.026465907331998335,
      0.0017583319323150341,
    ],
    [
      0.04152906589960523,
      0.044025552524932406,
      -0.009669682279354514,
      0.046736871369353235,
      0.03877302528270452,
      0.012336459551975156,
    ],
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

  const drawInitialGradient = () => {
    const container = document.getElementById("initial_gradient");
    if (!container) {
      return;
    }

    const width = 640;
    const height = 680;
    const radius = 32;
    const xPositions = [170, 470];
    const yPositions = Array.from({ length: 6 }, (_, index) => 100 + index * 102);
    const svg = createSvgElement("svg", {
      class: "nndl-plot nndl-gradient-diagram",
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-labelledby": "initial-gradient-title initial-gradient-description",
    });

    svg.append(
      createSvgElement(
        "title",
        { id: "initial-gradient-title" },
        "Initial gradient by hidden layer",
      ),
      createSvgElement(
        "desc",
        { id: "initial-gradient-description" },
        "Two connected layers of six neurons. Orange bars show that gradients are usually larger in hidden layer two.",
      ),
    );

    const definitions = createSvgElement("defs");
    const marker = createSvgElement("marker", {
      id: "nndl-network-arrow",
      viewBox: "0 0 8 8",
      refX: 7,
      refY: 4,
      markerWidth: 5,
      markerHeight: 5,
      orient: "auto-start-reverse",
    });
    marker.append(
      createSvgElement("path", {
        class: "nndl-network-arrow",
        d: "M 0 0 L 8 4 L 0 8 z",
      }),
    );
    definitions.append(marker);
    svg.append(definitions);

    xPositions.forEach((x, index) => {
      svg.append(
        createSvgElement(
          "text",
          {
            class: "nndl-network-label",
            x,
            y: 38,
            "text-anchor": "middle",
          },
          `Hidden layer ${index + 1}`,
        ),
      );
    });

    const connections = createSvgElement("g", { "aria-hidden": "true" });
    yPositions.forEach((fromY) => {
      yPositions.forEach((toY) => {
        const deltaX = xPositions[1] - xPositions[0];
        const deltaY = toY - fromY;
        const length = Math.hypot(deltaX, deltaY);
        const unitX = deltaX / length;
        const unitY = deltaY / length;
        connections.append(
          createSvgElement("line", {
            class: "nndl-network-connection",
            x1: xPositions[0] + unitX * radius,
            y1: fromY + unitY * radius,
            x2: xPositions[1] - unitX * (radius + 7),
            y2: toY - unitY * (radius + 7),
            "marker-end": "url(#nndl-network-arrow)",
          }),
        );
      });
    });
    svg.append(connections);

    xPositions.forEach((x, layerIndex) => {
      yPositions.forEach((y, neuronIndex) => {
        svg.append(
          createSvgElement("circle", {
            class: "nndl-network-neuron",
            cx: x,
            cy: y,
            r: radius,
            "aria-hidden": "true",
          }),
          createSvgElement("line", {
            class: "nndl-network-baseline",
            x1: x - 13,
            x2: x + 13,
            y1: y,
            y2: y,
            "aria-hidden": "true",
          }),
          createSvgElement("line", {
            class: "nndl-network-gradient",
            x1: x,
            x2: x,
            y1: y,
            y2: y - gradientValues[layerIndex][neuronIndex] * 560,
            "aria-hidden": "true",
          }),
        );
      });
    });

    container.replaceChildren(svg);
    container.classList.add("is-enhanced");
  };

  const drawSigmoidPrime = () => {
    const points = Array.from({ length: 201 }, (_, index) => {
      const x = -5 + (10 * index) / 200;
      const sigmoid = 1 / (1 + Math.exp(-x));
      return [x, sigmoid * (1 - sigmoid)];
    });
    window.NNDLPlots.drawPlot({
      id: "sigmoid_prime_graph",
      title: "Derivative of sigmoid function",
      description:
        "The sigmoid derivative peaks at one quarter when z equals zero and approaches zero in both directions.",
      points,
      yDomain: [0, 0.25],
      yTicks: [0, 0.05, 0.1, 0.15, 0.2, 0.25],
      yTickFormat: (value) => value.toFixed(2),
    });
  };

  if (window.NNDLPlots) {
    window.NNDLPlots.onReady(() => {
      drawInitialGradient();
      drawSigmoidPrime();
    });
  }
})();
