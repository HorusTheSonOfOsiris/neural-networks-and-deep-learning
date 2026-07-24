(() => {
  const data = [
    [0.7, 1.8],
    [1.3, 2.2],
    [1.9, 4.0],
    [2.6, 5.0],
    [2.9, 6.1],
    [3.6, 7.0],
    [3.8, 7.4],
    [3.95, 8.0],
    [4.4, 9.1],
    [4.9, 10.0],
  ];

  const sample = (start, end, count, fn) =>
    Array.from({ length: count + 1 }, (_, index) => {
      const x = start + ((end - start) * index) / count;
      return [x, fn(x)];
    });

  const polynomial = (x) =>
    2.20539187e-1 * x ** 9 -
    5.49142821 * x ** 8 +
    5.87844045e1 * x ** 7 -
    3.53892824e2 * x ** 6 +
    1.31549254e3 * x ** 5 -
    3.11809836e3 * x ** 4 +
    4.69080366e3 * x ** 3 -
    4.29612493e3 * x ** 2 +
    2.16228823e3 * x -
    4.50983951e2;

  const gaussian = (sigma) => (x) =>
    Math.exp(-(x * x) / (2 * sigma * sigma)) /
    (sigma * Math.sqrt(2 * Math.PI));

  const commonModelOptions = {
    description:
      "Ten sample observations plotted with x from zero to five and y from zero to ten.",
    xDomain: [0, 5],
    yDomain: [0, 10],
    xTicks: [0, 1, 2, 3, 4, 5],
    yTicks: [0, 2, 4, 6, 8, 10],
    xLabel: "x",
    yLabel: "y",
    yTickFormat: String,
    scatterPoints: data,
  };

  const plots = [
    {
      ...commonModelOptions,
      id: "simple_model",
      title: "Sample data",
      points: [],
    },
    {
      ...commonModelOptions,
      id: "polynomial_fit",
      title: "Exact polynomial fit",
      description:
        "A ninth-degree polynomial passes through all ten sample observations.",
      points: sample(0, 5, 500, polynomial),
    },
    {
      ...commonModelOptions,
      id: "linear_fit",
      title: "Linear model",
      description:
        "The line y equals two x closely fits the ten sample observations.",
      points: [
        [0, 0],
        [5, 10],
      ],
    },
    {
      id: "wide_gaussian",
      title: "Wide Gaussian distribution",
      description:
        "A broad Gaussian distribution with standard deviation square root of 501.",
      points: sample(-30, 30, 400, gaussian(Math.sqrt(501))),
      xDomain: [-30, 30],
      yDomain: [0, 0.02],
      xTicks: [-30, -15, 0, 15, 30],
      yTicks: [0, 0.01, 0.02],
      yAxisAt: 0,
      xLabel: "z",
      yTickFormat: (value) => value.toFixed(2),
    },
    {
      id: "narrow_gaussian",
      title: "Narrow Gaussian distribution",
      description:
        "A sharply peaked Gaussian distribution with standard deviation square root of 1.5.",
      points: sample(-30, 30, 400, gaussian(Math.sqrt(1.5))),
      xDomain: [-30, 30],
      yDomain: [0, 0.4],
      xTicks: [-30, -15, 0, 15, 30],
      yTicks: [0, 0.1, 0.2, 0.3, 0.4],
      yAxisAt: 0,
      xLabel: "z",
      yTickFormat: (value) => value.toFixed(1),
    },
    {
      id: "tanh",
      title: "tanh function",
      description:
        "The hyperbolic tangent rises smoothly from minus one to one.",
      points: sample(-5, 5, 200, Math.tanh),
      xDomain: [-5, 5],
      yDomain: [-1, 1],
      xTicks: [-4, -3, -2, -1, 0, 1, 2, 3, 4],
      yTicks: [-1, -0.5, 0, 0.5, 1],
      xAxisAt: 0,
      xLabel: "z",
      yTickFormat: (value) => value.toFixed(1),
    },
    {
      id: "relu",
      title: "max(0, z)",
      description:
        "The rectified linear function is zero for negative z and equals z for positive z.",
      points: [
        [-5, 0],
        [0, 0],
        [5, 5],
      ],
      xDomain: [-5, 5],
      yDomain: [-5, 5],
      xTicks: [-4, -3, -2, -1, 0, 1, 2, 3, 4],
      yTicks: [-4, -3, -2, -1, 0, 1, 2, 3, 4],
      xAxisAt: 0,
      xLabel: "z",
      yTickFormat: String,
    },
  ];

  if (window.NNDLPlots) {
    window.NNDLPlots.onReady(() => plots.forEach(window.NNDLPlots.drawPlot));
  }
})();
