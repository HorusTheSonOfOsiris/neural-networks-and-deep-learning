"""
mnist_loader
~~~~~~~~~~~~

A library to load the MNIST image data.  For details of the data
structures that are returned, see the doc strings for ``load_data``
and ``load_data_wrapper``.  In practice, ``load_data_wrapper`` is the
function usually called by our neural network code.

Python 3 port of Michael Nielsen's original ``mnist_loader.py``
(Python 2.7). See ``code/python3/PROVENANCE.md`` for the source and
license, and ``code/python3/README.md`` for how to obtain the
``mnist.pkl.gz`` data file this module expects.

Port changes from the original (mechanical only, no algorithm
changes):
  - ``cPickle`` -> ``pickle``.
  - ``pickle.load(f, encoding='latin1')`` instead of bare
    ``cPickle.load(f)``: the ``mnist.pkl.gz`` file was pickled under
    Python 2, and its numpy arrays cannot be unpickled under Python 3
    without specifying a legacy string encoding. This is a mechanical
    requirement for cross-version compatibility, not a behavioral
    change.
  - ``zip(...)`` wrapped in ``list(...)`` in ``load_data_wrapper``:
    the returned ``training_data`` / ``validation_data`` / ``test_data``
    are shuffled and sliced by ``network.py``/``network2.py`` (via
    ``random.shuffle`` and list slicing), which requires a list. In
    Python 2, ``zip`` already returned a list; in Python 3 it returns
    a one-shot iterator, so this wrap is required to preserve the
    original behavior.
  - The hardcoded relative path ``'../data/mnist.pkl.gz'`` is now
    configurable (function argument, falling back to the
    ``MNIST_DATA_PATH`` environment variable, falling back to
    ``code/python3/data/mnist.pkl.gz`` next to this file) so the
    module works regardless of the caller's current working
    directory. See PROVENANCE.md for how to obtain the data file.
"""

#### Libraries
# Standard library
import os
import pickle
import gzip

# Third-party libraries
import numpy as np

# Default location of the MNIST data file, relative to this module.
_DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "mnist.pkl.gz"
)


def _resolve_data_path(path=None):
    """Resolve the path to ``mnist.pkl.gz``.

    Precedence: explicit ``path`` argument > ``MNIST_DATA_PATH``
    environment variable > ``code/python3/data/mnist.pkl.gz`` next to
    this module. This is a port-only convenience (the original hardcoded
    ``'../data/mnist.pkl.gz'``); see PROVENANCE.md.
    """
    if path is not None:
        return path
    return os.environ.get("MNIST_DATA_PATH", _DEFAULT_DATA_PATH)


def load_data(path=None):
    """Return the MNIST data as a tuple containing the training data,
    the validation data, and the test data.

    The ``training_data`` is returned as a tuple with two entries.
    The first entry contains the actual training images.  This is a
    numpy ndarray with 50,000 entries.  Each entry is, in turn, a
    numpy ndarray with 784 values, representing the 28 * 28 = 784
    pixels in a single MNIST image.

    The second entry in the ``training_data`` tuple is a numpy ndarray
    containing 50,000 entries.  Those entries are just the digit
    values (0...9) for the corresponding images contained in the first
    entry of the tuple.

    The ``validation_data`` and ``test_data`` are similar, except
    each contains only 10,000 images.

    This is a nice data format, but for use in neural networks it's
    helpful to modify the format of the ``training_data`` a little.
    That's done in the wrapper function ``load_data_wrapper()``, see
    below.
    """
    f = gzip.open(_resolve_data_path(path), 'rb')
    training_data, validation_data, test_data = pickle.load(f, encoding='latin1')
    f.close()
    return (training_data, validation_data, test_data)

def load_data_wrapper(path=None):
    """Return a tuple containing ``(training_data, validation_data,
    test_data)``. Based on ``load_data``, but the format is more
    convenient for use in our implementation of neural networks.

    In particular, ``training_data`` is a list containing 50,000
    2-tuples ``(x, y)``.  ``x`` is a 784-dimensional numpy.ndarray
    containing the input image.  ``y`` is a 10-dimensional
    numpy.ndarray representing the unit vector corresponding to the
    correct digit for ``x``.

    ``validation_data`` and ``test_data`` are lists containing 10,000
    2-tuples ``(x, y)``.  In each case, ``x`` is a 784-dimensional
    numpy.ndarry containing the input image, and ``y`` is the
    corresponding classification, i.e., the digit values (integers)
    corresponding to ``x``.

    Obviously, this means we're using slightly different formats for
    the training data and the validation / test data.  These formats
    turn out to be the most convenient for use in our neural network
    code."""
    tr_d, va_d, te_d = load_data(path)
    training_inputs = [np.reshape(x, (784, 1)) for x in tr_d[0]]
    training_results = [vectorized_result(y) for y in tr_d[1]]
    training_data = list(zip(training_inputs, training_results))
    validation_inputs = [np.reshape(x, (784, 1)) for x in va_d[0]]
    validation_data = list(zip(validation_inputs, va_d[1]))
    test_inputs = [np.reshape(x, (784, 1)) for x in te_d[0]]
    test_data = list(zip(test_inputs, te_d[1]))
    return (training_data, validation_data, test_data)

def vectorized_result(j):
    """Return a 10-dimensional unit vector with a 1.0 in the jth
    position and zeroes elsewhere.  This is used to convert a digit
    (0...9) into a corresponding desired output from the neural
    network."""
    e = np.zeros((10, 1))
    e[j] = 1.0
    return e
