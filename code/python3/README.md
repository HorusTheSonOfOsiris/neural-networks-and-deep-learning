# Python 3 companion code port

This directory is an **optional**, community-ported, Python 3.13
version of the neural network code that accompanies Michael Nielsen's
book *Neural Networks and Deep Learning*.

**The book text itself (under `docs/`) keeps Nielsen's original
Python 2.7 code listings verbatim** — that's the source of record and
is not touched by this directory. This is purely a convenience port
for readers who want to actually run the examples on a modern Python
install. See Plan.md §1 and §5 (ticket P5-1) for why this exists and
what its scope is.

## Attribution

This code is a mechanical Python 3 port of code samples written by
**Michael Nielsen** for his book *Neural Networks and Deep Learning*
(<http://neuralnetworksanddeeplearning.com>).

- Original repository: <https://github.com/mnielsen/neural-networks-and-deep-learning>
- License: **MIT** (see `PROVENANCE.md` for the full text and the
  license-check finding, and for exactly which commit was ported)

This port is unaffiliated with and not endorsed by Michael Nielsen.
See `PROVENANCE.md` for full details on what was ported, from where,
under what license, and exactly what mechanical changes were made
(xrange -> range, print statements -> print(), cPickle -> pickle,
etc. — no algorithm changes).

## Files

| File               | Status                                                                 |
| ------------------ | ----------------------------------------------------------------------|
| `mnist_loader.py`  | Fully ported, working. Loads MNIST data (see below).                  |
| `network.py`       | Fully ported, working. Chapter 1's basic SGD network.                 |
| `network2.py`      | Fully ported, working. Cross-entropy cost, regularization, etc.       |
| `network3.py`      | Mechanically ported only. Targets the **original Theano API** (0.6/0.7). Theano is unmaintained/dead and not expected to run on a modern install. Provided for reference/reading, not execution. See the header comment in the file. |

## Installing dependencies

This is a separate, optional deliverable from the main site-generation
tooling, so its dependencies are **not** added to the root
`pyproject.toml`. Install them from `code/python3/requirements.txt`
instead, e.g.:

```bash
# with uv (creates/uses a venv automatically)
uv run --with-requirements code/python3/requirements.txt python code/python3/tests/smoke_test.py

# or, with a plain venv
python3 -m venv .venv-py3port
source .venv-py3port/bin/activate
pip install -r code/python3/requirements.txt
```

## Getting the MNIST data

None of the code here bundles MNIST data (it's a large binary blob and
is intentionally not committed to this repository). See
`PROVENANCE.md` → "Getting the MNIST data file" for exactly how to
fetch `mnist.pkl.gz` and where to put it (default expected location:
`code/python3/data/mnist.pkl.gz`, override with the `MNIST_DATA_PATH`
environment variable or an explicit `path=` argument).

## Running it

```python
import sys
sys.path.insert(0, "code/python3")

import mnist_loader
import network

training_data, validation_data, test_data = mnist_loader.load_data_wrapper()

net = network.Network([784, 30, 10])
net.SGD(training_data, epochs=30, mini_batch_size=10, eta=3.0, test_data=test_data)
```

`network2.py` follows the same pattern with more options (cost
function, regularization, monitoring flags) — see its module and
`Network.SGD` docstrings.

## Smoke test

`code/python3/tests/smoke_test.py` trains `network.py` for one epoch
on a 1,000-image subset of MNIST and asserts it runs end-to-end
without crashing (it does not assert on accuracy — one epoch on 1k
images is not expected to be a good classifier, just a working one).

If `mnist.pkl.gz` cannot be found (see "Getting the MNIST data"
above), the smoke test **skips** with a clear message rather than
failing, since the data file is not committed to this repository.

Run it with:

```bash
uv run --with-requirements code/python3/requirements.txt python code/python3/tests/smoke_test.py
```

or, with pytest, if installed:

```bash
uv run --with-requirements code/python3/requirements.txt --with pytest pytest code/python3/tests/smoke_test.py -v
```
