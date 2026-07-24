(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 720;
  const NODE_RADIUS = 27;

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

  const sample = (start, end, count, fn) =>
    Array.from({ length: count + 1 }, (_, index) => {
      const x = start + ((end - start) * index) / count;
      return [x, fn(x)];
    });

  const sigmoid = (value) => 1 / (1 + Math.exp(-value));
  const sampleFunction = (x) =>
    0.2 +
    0.4 * x * x +
    0.3 * x * Math.sin(15 * x) +
    0.05 * Math.cos(50 * x);
  const inverseSampleFunction = (x) => {
    const value = sampleFunction(x);
    return Math.log(value / (1 - value));
  };
  const sigmoidLike = (value) =>
    sigmoid(value) +
    0.2 * Math.sin(10 * value) * Math.exp(-Math.abs(value));

  const sampleFunctionPoints = sample(0, 1, 400, sampleFunction);
  const inverseFunctionPoints = sample(0, 1, 400, inverseSampleFunction);

  const plots = [
    ...["function", "function_2", "function_3"].map((id) => ({
      id,
      title: "A continuous function f(x)",
      description:
        "A complicated continuous function varying over the interval from zero to one.",
      points: sampleFunctionPoints,
      xDomain: [0, 1],
      yDomain: [0, 1],
      xTicks: [0, 0.2, 0.4, 0.6, 0.8, 1],
      yTicks: [0, 0.2, 0.4, 0.6, 0.8, 1],
      xLabel: "x",
      yLabel: "f(x)",
      xAxisAt: 0,
      yAxisAt: 0,
      yTickFormat: (value) => value.toFixed(1),
    })),
    ...["inverted_function", "inverted_function_2"].map((id) => ({
      id,
      title: "Inverse-sigmoid target",
      description:
        "The function sigma inverse composed with the target function f of x.",
      points: inverseFunctionPoints,
      xDomain: [0, 1],
      yDomain: [-2, 2],
      xTicks: [0, 0.2, 0.4, 0.6, 0.8, 1],
      yTicks: [-2, -1, 0, 1, 2],
      xLabel: "x",
      yLabel: "σ⁻¹ ∘ f(x)",
      xAxisAt: 0,
      yAxisAt: 0,
      yTickFormat: String,
    })),
    {
      id: "sigmoid",
      title: "Sigmoid activation σ(z)",
      description:
        "The sigmoid activation rises smoothly from zero to one.",
      points: sample(-3, 3, 400, sigmoid),
      xDomain: [-3, 3],
      yDomain: [0, 1],
      xTicks: [-3, -2, -1, 0, 1, 2, 3],
      yTicks: [0, 0.2, 0.4, 0.6, 0.8, 1],
      xLabel: "z",
      xAxisAt: 0,
      yAxisAt: 0,
      yTickFormat: (value) => value.toFixed(1),
    },
    {
      id: "sigmoid_like",
      title: "A sigmoid-like activation s(z)",
      description:
        "A non-sigmoid activation with small oscillations that still approaches zero and one.",
      points: sample(-3, 3, 600, sigmoidLike),
      xDomain: [-3, 3],
      yDomain: [0, 1],
      xTicks: [-3, -2, -1, 0, 1, 2, 3],
      yTicks: [0, 0.2, 0.4, 0.6, 0.8, 1],
      xLabel: "z",
      xAxisAt: 0,
      yAxisAt: 0,
      yTickFormat: (value) => value.toFixed(1),
    },
    {
      id: "failure",
      title: "Narrow window of failure",
      description:
        "A steep sigmoid approximates a step except in a narrow interval around x equals one half.",
      points: sample(0, 1, 400, (x) => sigmoid(50 * x - 25)),
      xDomain: [0, 1],
      yDomain: [0, 1],
      xTicks: [0, 0.25, 0.5, 0.75, 1],
      yTicks: [0, 0.5, 1],
      xLabel: "x",
      xAxisAt: 0,
      yAxisAt: 0,
      yTickFormat: (value) => value.toFixed(1),
    },
  ];

  const layerPositions = (count, height) => {
    if (count === 1) {
      return [height / 2];
    }
    const padding = 58;
    const step = (height - 2 * padding) / (count - 1);
    return Array.from({ length: count }, (_, index) => padding + index * step);
  };

  const labelFor = (labels, index) =>
    labels && labels[index] ? labels[index] : "";

  const drawNetwork = ({
    id,
    title,
    description,
    inputs,
    hidden,
    outputs,
    inputLabels = [],
    hiddenLabels = [],
    outputLabels = [],
    connections,
  }) => {
    const container = document.getElementById(id);
    if (!container) {
      return;
    }

    const maximumLayerSize = Math.max(inputs, hidden || 0, outputs);
    const height = Math.max(280, maximumLayerSize * 78 + 70);
    const titleId = `${id}-title`;
    const descriptionId = `${id}-description`;
    const svg = svgElement("svg", {
      class: "nndl-plot nndl-chap4-network",
      viewBox: `0 0 ${WIDTH} ${height}`,
      role: "img",
      "aria-labelledby": `${titleId} ${descriptionId}`,
    });
    svg.append(
      svgElement("title", { id: titleId }, title),
      svgElement("desc", { id: descriptionId }, description),
      svgElement(
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

    const hasHiddenLayer = hidden > 0;
    const inputX = hasHiddenLayer ? 105 : 220;
    const hiddenX = 360;
    const outputX = hasHiddenLayer ? 615 : 500;
    const inputY = layerPositions(inputs, height);
    const hiddenY = hasHiddenLayer ? layerPositions(hidden, height) : [];
    const outputY = layerPositions(outputs, height);
    const layerNodes = {
      input: inputY.map((y) => [inputX, y]),
      hidden: hiddenY.map((y) => [hiddenX, y]),
      output: outputY.map((y) => [outputX, y]),
    };
    const lineGroup = svgElement("g", { "aria-hidden": "true" });

    const connect = (from, to) => {
      const [x1, y1] = from;
      const [x2, y2] = to;
      const distance = Math.hypot(x2 - x1, y2 - y1);
      const offsetX = ((x2 - x1) / distance) * NODE_RADIUS;
      const offsetY = ((y2 - y1) / distance) * NODE_RADIUS;
      lineGroup.append(
        svgElement("line", {
          class: "nndl-network-connection",
          x1: x1 + offsetX,
          y1: y1 + offsetY,
          x2: x2 - offsetX,
          y2: y2 - offsetY,
        }),
      );
    };

    if (connections) {
      connections(layerNodes).forEach(([from, to]) => connect(from, to));
    } else if (hasHiddenLayer) {
      layerNodes.input.forEach((from) => {
        layerNodes.hidden.forEach((to) => connect(from, to));
      });
      layerNodes.hidden.forEach((from) => {
        layerNodes.output.forEach((to) => connect(from, to));
      });
    } else {
      layerNodes.input.forEach((from) => {
        layerNodes.output.forEach((to) => connect(from, to));
      });
    }
    svg.append(lineGroup);

    const drawLayer = (nodes, labels, layerName) => {
      const group = svgElement("g");
      nodes.forEach(([x, y], index) => {
        group.append(
          svgElement("circle", {
            class: "nndl-network-neuron",
            cx: x,
            cy: y,
            r: NODE_RADIUS,
          }),
        );
        const label = labelFor(labels, index);
        if (label) {
          group.append(
            svgElement(
              "text",
              {
                class: "nndl-network-label",
                x,
                y: y + 5,
                "text-anchor": "middle",
              },
              label,
            ),
          );
        }
      });
      group.append(
        svgElement(
          "text",
          {
            class: "nndl-network-layer-label",
            x: nodes[0][0],
            y: height - 16,
            "text-anchor": "middle",
          },
          layerName,
        ),
      );
      svg.append(group);
    };

    drawLayer(layerNodes.input, inputLabels, "Input");
    if (hasHiddenLayer) {
      drawLayer(layerNodes.hidden, hiddenLabels, "Hidden");
    }
    drawLayer(layerNodes.output, outputLabels, "Output");
    container.replaceChildren(svg);
    container.classList.add("is-enhanced");
  };

  const networks = [
    {
      id: "basic_network",
      title: "One-input neural network",
      description:
        "One input connects to three hidden neurons, which connect to one output.",
      inputs: 1,
      hidden: 3,
      outputs: 1,
      inputLabels: ["x"],
      outputLabels: ["f(x)"],
    },
    {
      id: "vector_valued_network",
      title: "A vector-valued neural network",
      description:
        "Three inputs connect through five hidden neurons to two outputs.",
      inputs: 3,
      hidden: 5,
      outputs: 2,
      inputLabels: ["x₁", "x₂", "x₃"],
      outputLabels: ["f¹(x)", "f²(x)"],
    },
    {
      id: "bigger_network",
      title: "A wider hidden layer",
      description:
        "One input connects through five hidden neurons to one output.",
      inputs: 1,
      hidden: 5,
      outputs: 1,
      inputLabels: ["x"],
      outputLabels: ["f(x)"],
    },
    {
      id: "two_hidden_neurons",
      title: "Two-neuron hidden layer",
      description:
        "One input connects through two hidden neurons to one output.",
      inputs: 1,
      hidden: 2,
      outputs: 1,
      inputLabels: ["x"],
    },
    {
      id: "two_inputs",
      title: "A neuron with two inputs",
      description:
        "Inputs x and y, with weights w one and w two, connect to a single sigmoid neuron.",
      inputs: 2,
      hidden: 0,
      outputs: 1,
      inputLabels: ["x", "y"],
      outputLabels: ["σ"],
    },
    {
      id: "tower_n_dim",
      title: "A three-variable tower network",
      description:
        "Each of three inputs connects to a pair of step neurons; all six feed one output.",
      inputs: 3,
      hidden: 6,
      outputs: 1,
      inputLabels: ["x₁", "x₂", "x₃"],
      hiddenLabels: ["s₁", "t₁", "s₂", "t₂", "s₃", "t₃"],
      connections: ({ input, hidden, output }) => [
        [input[0], hidden[0]],
        [input[0], hidden[1]],
        [input[1], hidden[2]],
        [input[1], hidden[3]],
        [input[2], hidden[4]],
        [input[2], hidden[5]],
        ...hidden.map((node) => [node, output[0]]),
      ],
    },
  ];

  const render = () => {
    if (window.NNDLPlots) {
      plots.forEach(window.NNDLPlots.drawPlot);
    }
    networks.forEach(drawNetwork);
  };

  if (window.NNDLPlots) {
    window.NNDLPlots.onReady(render);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, { once: true });
  } else {
    render();
  }
})();
