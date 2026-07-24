(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const SUBSCRIPTS = ["₁", "₂", "₃", "₄"];
  const LEARNING_CONFIGS = [
    {
      id: "saturation1",
      costName: "Quadratic cost",
      startingWeight: 0.6,
      startingBias: 0.9,
      eta: 0.15,
      cost: (activation) => (activation * activation) / 2,
      derivative: (activation) =>
        activation * activation * (1 - activation),
    },
    {
      id: "saturation2",
      costName: "Quadratic cost",
      startingWeight: 2,
      startingBias: 2,
      eta: 0.15,
      cost: (activation) => (activation * activation) / 2,
      derivative: (activation) =>
        activation * activation * (1 - activation),
    },
    {
      id: "saturation3",
      costName: "Cross-entropy cost",
      startingWeight: 0.6,
      startingBias: 0.9,
      eta: 0.005,
      cost: (activation) => -Math.log(1 - activation),
      derivative: (activation) => 1 / (1 - activation),
    },
    {
      id: "saturation4",
      costName: "Cross-entropy cost",
      startingWeight: 2,
      startingBias: 2,
      eta: 0.005,
      cost: (activation) => -Math.log(1 - activation),
      derivative: (activation) => 1 / (1 - activation),
    },
  ];
  const EPOCHS = 300;
  const ANIMATION_DURATION = 5000;

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
  const signed = (value) => `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;

  const createMetric = (label, initialValue) => {
    const metric = element("div", "nndl-widget-metric");
    const term = element("span", "nndl-widget-metric-label", label);
    const value = element("output", "nndl-widget-metric-value", initialValue);
    metric.append(term, value);
    return { metric, value };
  };

  const createCostChart = (id, costName, maximumCost) => {
    const width = 600;
    const height = 250;
    const margin = { top: 24, right: 22, bottom: 48, left: 64 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const scaleX = (epoch) => margin.left + (epoch / EPOCHS) * plotWidth;
    const scaleY = (cost) =>
      margin.top + (1 - cost / maximumCost) * plotHeight;
    const titleId = `${id}-chart-title`;
    const descriptionId = `${id}-chart-description`;
    const svg = svgElement("svg", {
      class: "nndl-learning-chart",
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-labelledby": `${titleId} ${descriptionId}`,
    });
    const path = svgElement("path", {
      class: "nndl-learning-cost-line",
      d: "",
    });

    svg.append(
      svgElement("title", { id: titleId }, `${costName} during learning`),
      svgElement(
        "desc",
        { id: descriptionId },
        "Cost falls as the neuron learns over 300 epochs.",
      ),
    );

    [0, 0.5, 1].forEach((fraction) => {
      const y = margin.top + fraction * plotHeight;
      const cost = maximumCost * (1 - fraction);
      svg.append(
        svgElement("line", {
          class: "nndl-learning-gridline",
          x1: margin.left,
          x2: width - margin.right,
          y1: y,
          y2: y,
          "aria-hidden": "true",
        }),
        svgElement(
          "text",
          {
            class: "nndl-learning-tick",
            x: margin.left - 10,
            y: y + 4,
            "text-anchor": "end",
          },
          cost.toFixed(cost >= 1 ? 1 : 2),
        ),
      );
    });

    [0, 150, 300].forEach((epoch) => {
      const x = scaleX(epoch);
      svg.append(
        svgElement(
          "text",
          {
            class: "nndl-learning-tick",
            x,
            y: height - 22,
            "text-anchor": "middle",
          },
          String(epoch),
        ),
      );
    });

    svg.append(
      svgElement("line", {
        class: "nndl-learning-axis",
        x1: margin.left,
        x2: margin.left,
        y1: margin.top,
        y2: height - margin.bottom,
        "aria-hidden": "true",
      }),
      svgElement("line", {
        class: "nndl-learning-axis",
        x1: margin.left,
        x2: width - margin.right,
        y1: height - margin.bottom,
        y2: height - margin.bottom,
        "aria-hidden": "true",
      }),
      svgElement(
        "text",
        {
          class: "nndl-learning-label",
          x: 18,
          y: margin.top + plotHeight / 2,
          "text-anchor": "middle",
          transform: `rotate(-90 18 ${margin.top + plotHeight / 2})`,
        },
        "Cost",
      ),
      svgElement(
        "text",
        {
          class: "nndl-learning-label",
          x: margin.left + plotWidth / 2,
          y: height - 4,
          "text-anchor": "middle",
        },
        "Epoch",
      ),
      path,
    );

    const draw = (points) => {
      const pathData = points
        .map(
          ([epoch, cost], index) =>
            `${index === 0 ? "M" : "L"} ${scaleX(epoch).toFixed(2)} ${scaleY(
              Math.min(cost, maximumCost),
            ).toFixed(2)}`,
        )
        .join(" ");
      path.setAttribute("d", pathData);
    };

    return { svg, draw };
  };

  const enhanceLearningWidget = (config) => {
    const container = document.getElementById(config.id);
    if (!container) {
      return;
    }

    const card = element("section", "nndl-learning-widget");
    const header = element("div", "nndl-widget-header");
    const headingGroup = element("div");
    const eyebrow = element(
      "p",
      "nndl-widget-eyebrow",
      "Single-neuron learning",
    );
    const heading = element("p", "nndl-widget-title", config.costName);
    const detail = element(
      "p",
      "nndl-widget-detail",
      `Target 0 · learning rate η = ${config.eta}`,
    );
    headingGroup.append(eyebrow, heading, detail);

    const runButton = element("button", "nndl-widget-button", "Run");
    runButton.type = "button";
    header.append(headingGroup, runButton);

    const flow = element("div", "nndl-learning-flow");
    const input = element("span", "nndl-learning-node-label", "Input 1.0");
    const inputArrow = element("span", "nndl-learning-arrow", "→");
    const neuron = element("span", "nndl-learning-neuron", "σ");
    const outputArrow = element("span", "nndl-learning-arrow", "→");
    const output = element("output", "nndl-learning-node-label", "Output 0.00");
    flow.append(input, inputArrow, neuron, outputArrow, output);

    const metrics = element("div", "nndl-widget-metrics");
    const weightMetric = createMetric("Weight w", "");
    const biasMetric = createMetric("Bias b", "");
    const epochMetric = createMetric("Epoch", "0");
    const costMetric = createMetric("Cost", "");
    metrics.append(
      weightMetric.metric,
      biasMetric.metric,
      epochMetric.metric,
      costMetric.metric,
    );

    const initialActivation = sigmoid(
      config.startingWeight + config.startingBias,
    );
    const initialCost = config.cost(initialActivation);
    const chart = createCostChart(
      config.id,
      config.costName,
      initialCost * 1.08,
    );
    const status = element(
      "p",
      "nndl-widget-status",
      "Ready to train for 300 epochs.",
    );
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    card.append(header, flow, metrics, chart.svg, status);

    let weight = config.startingWeight;
    let bias = config.startingBias;
    let epoch = 0;
    let points = [];
    let animationFrame = null;

    const updateDisplay = () => {
      const activation = sigmoid(weight + bias);
      const cost = config.cost(activation);
      weightMetric.value.value = signed(weight);
      weightMetric.value.textContent = signed(weight);
      biasMetric.value.value = signed(bias);
      biasMetric.value.textContent = signed(bias);
      epochMetric.value.value = String(epoch);
      epochMetric.value.textContent = String(epoch);
      costMetric.value.value = cost.toFixed(4);
      costMetric.value.textContent = cost.toFixed(4);
      output.value = activation.toFixed(2);
      output.textContent = `Output ${activation.toFixed(2)}`;
      chart.draw(points);
    };

    const reset = () => {
      weight = config.startingWeight;
      bias = config.startingBias;
      epoch = 0;
      points = [[0, config.cost(sigmoid(weight + bias))]];
      updateDisplay();
    };

    const trainOnce = () => {
      const activation = sigmoid(weight + bias);
      const delta = config.derivative(activation);
      weight -= config.eta * delta;
      bias -= config.eta * delta;
      epoch += 1;
      points.push([epoch, config.cost(sigmoid(weight + bias))]);
    };

    const finish = () => {
      animationFrame = null;
      updateDisplay();
      runButton.disabled = false;
      runButton.textContent = "Run again";
      status.textContent = `Complete. Output fell to ${sigmoid(
        weight + bias,
      ).toFixed(2)} after ${EPOCHS} epochs.`;
    };

    const run = () => {
      if (animationFrame !== null) {
        cancelAnimationFrame(animationFrame);
      }
      reset();
      runButton.disabled = true;
      runButton.textContent = "Running…";
      status.textContent = "Training in progress.";

      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        while (epoch < EPOCHS) {
          trainOnce();
        }
        finish();
        return;
      }

      let startedAt = null;
      const animate = (timestamp) => {
        if (startedAt === null) {
          startedAt = timestamp;
        }
        const progress = Math.min(
          1,
          (timestamp - startedAt) / ANIMATION_DURATION,
        );
        const targetEpoch = Math.floor(progress * EPOCHS);
        while (epoch < targetEpoch) {
          trainOnce();
        }
        updateDisplay();

        if (epoch < EPOCHS) {
          animationFrame = requestAnimationFrame(animate);
        } else {
          finish();
        }
      };
      animationFrame = requestAnimationFrame(animate);
    };

    runButton.addEventListener("click", run);
    reset();
    container.replaceChildren(card);
    container.classList.add("is-enhanced");
  };

  const enhanceSoftmax = () => {
    const containers = Array.from(
      { length: 4 },
      (_, index) => document.getElementById(`smG${index + 1}`),
    );
    const root = containers[0];
    if (!root) {
      return;
    }

    const initialValues = [2.5, -1, 3.2, 0.5];
    const panel = element("section", "nndl-softmax-panel");
    const headingId = "nndl-softmax-heading";
    panel.setAttribute("aria-labelledby", headingId);

    const header = element("div", "nndl-widget-header");
    const headingGroup = element("div");
    const eyebrow = element("p", "nndl-widget-eyebrow", "Softmax explorer");
    const heading = element("p", "nndl-widget-title", "Logits to probabilities");
    heading.id = headingId;
    const detail = element(
      "p",
      "nndl-widget-detail",
      "Move any weighted input z; all four activations update together.",
    );
    headingGroup.append(eyebrow, heading, detail);
    const total = element("output", "nndl-softmax-total", "Σa = 1.000");
    total.setAttribute("aria-live", "polite");
    header.append(headingGroup, total);

    const rows = element("div", "nndl-softmax-rows");
    const controls = initialValues.map((initialValue, index) => {
      const row = element("div", "nndl-softmax-row");
      const inputId = `nndl-softmax-z-${index + 1}`;
      const label = element(
        "label",
        "nndl-softmax-label",
        `z${SUBSCRIPTS[index]}`,
      );
      label.htmlFor = inputId;

      const range = element("input", "nndl-softmax-range");
      range.id = inputId;
      range.type = "range";
      range.min = "-5";
      range.max = "5";
      range.step = "0.1";
      range.value = String(initialValue);

      const value = element(
        "output",
        "nndl-softmax-logit",
        initialValue.toFixed(1),
      );
      value.setAttribute("for", inputId);

      const meter = element("span", "nndl-softmax-meter");
      const fill = element("span", "nndl-softmax-fill");
      meter.setAttribute("aria-hidden", "true");
      meter.append(fill);

      const probability = element(
        "output",
        "nndl-softmax-probability",
        `a${SUBSCRIPTS[index]} = 0.000`,
      );
      probability.setAttribute("for", inputId);

      row.append(label, range, value, meter, probability);
      rows.append(row);
      return { range, value, fill, probability };
    });

    const update = () => {
      const logits = controls.map(({ range }) => Number(range.value));
      const maximum = Math.max(...logits);
      const exponentials = logits.map((value) => Math.exp(value - maximum));
      const denominator = exponentials.reduce((sum, value) => sum + value, 0);
      const probabilities = exponentials.map((value) => value / denominator);

      controls.forEach((control, index) => {
        const probability = probabilities[index];
        control.value.value = logits[index].toFixed(1);
        control.value.textContent = logits[index].toFixed(1);
        control.fill.style.setProperty(
          "--nndl-probability",
          `${(probability * 100).toFixed(2)}%`,
        );
        control.probability.value = probability.toFixed(3);
        control.probability.textContent =
          `a${SUBSCRIPTS[index]} = ${probability.toFixed(3)}`;
      });
      total.value = probabilities
        .reduce((sum, value) => sum + value, 0)
        .toFixed(3);
      total.textContent = `Σa = ${total.value}`;
    };

    controls.forEach(({ range }) => range.addEventListener("input", update));
    panel.append(header, rows);
    root.replaceChildren(panel);
    root.classList.add("is-enhanced", "nndl-softmax-root");
    containers.slice(1).forEach((container) => {
      if (container) {
        container.hidden = true;
      }
    });
    update();
  };

  const render = () => {
    LEARNING_CONFIGS.forEach(enhanceLearningWidget);
    enhanceSoftmax();
  };

  if (window.NNDLPlots) {
    window.NNDLPlots.onReady(render);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, { once: true });
  } else {
    render();
  }
})();
