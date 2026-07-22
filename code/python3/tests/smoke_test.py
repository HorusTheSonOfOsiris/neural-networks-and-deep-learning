"""
smoke_test.py
~~~~~~~~~~~~~

Smoke test for the code/python3/ companion port (Plan.md ticket P5-1).

Trains ``network.py``'s ``Network`` for one epoch on a 1,000-image
subset of MNIST and asserts it runs end-to-end without crashing.
Accuracy is not asserted -- one epoch on 1,000 images is not expected
to produce a good classifier, only a working one.

If the MNIST data file (``mnist.pkl.gz``) cannot be found, this test
SKIPS with a clear message instead of failing, since the data file is
a large binary blob that is intentionally not committed to this
repository. See ../PROVENANCE.md for how to obtain it.

Usage:
    # standalone
    python code/python3/tests/smoke_test.py

    # via pytest
    pytest code/python3/tests/smoke_test.py -v
"""

import os
import sys

# Make the sibling package (mnist_loader.py, network.py) importable
# regardless of current working directory.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_DIR = os.path.dirname(_THIS_DIR)  # code/python3/
sys.path.insert(0, _PACKAGE_DIR)

SKIP_MESSAGE = (
    "MNIST data file not found -- skipping smoke test. "
    "Expected at '{path}' (or set the MNIST_DATA_PATH environment "
    "variable, or pass an explicit path). See code/python3/PROVENANCE.md "
    "-> 'Getting the MNIST data file' for how to obtain mnist.pkl.gz."
)


def _find_data_path():
    import mnist_loader
    return mnist_loader._resolve_data_path(None)


def _data_available():
    return os.path.isfile(_find_data_path())


def test_network_trains_one_epoch_without_crashing():
    """pytest entry point. Skips if MNIST data is unavailable."""
    if not _data_available():
        try:
            import pytest
            pytest.skip(SKIP_MESSAGE.format(path=_find_data_path()))
        except ImportError:
            print(SKIP_MESSAGE.format(path=_find_data_path()))
            return

    import mnist_loader
    import network

    training_data, validation_data, test_data = mnist_loader.load_data_wrapper()

    # 1k-image subset, per the P5-1 ticket.
    training_subset = training_data[:1000]
    test_subset = test_data[:200]

    net = network.Network([784, 30, 10])
    # Should run to completion without raising.
    net.SGD(training_subset, epochs=1, mini_batch_size=10, eta=3.0,
            test_data=test_subset)

    # Sanity check only: evaluate() should return an int in [0, len(test_subset)].
    score = net.evaluate(test_subset)
    assert isinstance(score, int)
    assert 0 <= score <= len(test_subset)


def _main():
    if not _data_available():
        print(SKIP_MESSAGE.format(path=_find_data_path()))
        print("SMOKE TEST SKIPPED (no MNIST data).")
        return 0

    import mnist_loader
    import network

    print("Loading MNIST data from: {}".format(_find_data_path()))
    training_data, validation_data, test_data = mnist_loader.load_data_wrapper()

    training_subset = training_data[:1000]
    test_subset = test_data[:200]
    print("Training on {} images, testing on {} images, 1 epoch...".format(
        len(training_subset), len(test_subset)))

    net = network.Network([784, 30, 10])
    net.SGD(training_subset, epochs=1, mini_batch_size=10, eta=3.0,
            test_data=test_subset)

    score = net.evaluate(test_subset)
    print("SMOKE TEST PASSED: trained 1 epoch end-to-end, "
          "test accuracy {} / {}".format(score, len(test_subset)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
