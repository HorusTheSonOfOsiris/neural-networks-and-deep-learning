# Provenance

This directory (`code/python3/`) is a Python 3.13 port of the companion
code for Michael Nielsen's book *Neural Networks and Deep Learning*.
The book's own text (under `docs/`) keeps the original Python 2.7 code
listings verbatim, for fidelity to the source. This directory is a
separate, optional, modernized companion, per Plan.md Phase 5 (P5-1).

## Source

- Repository: <https://github.com/mnielsen/neural-networks-and-deep-learning>
- Files ported: `src/mnist_loader.py`, `src/network.py`,
  `src/network2.py`, `src/network3.py`
- Commit used as source of record: `91b3fabf27f758fce4cef0ddc7f0e29b006a0c76`
  (last commit touching `src/`, authored 2017-09-28T17:08:17Z; the
  repository has not changed `src/` since)
- Fetched: 2026-07-22, via the GitHub REST API (`gh api
  repos/mnielsen/neural-networks-and-deep-learning/contents/src/...`)

## License finding

**License: MIT.** Permits vendoring/porting/modification.

The license text is embedded in the repository's `README.md` (there is
no standalone `LICENSE` file, which is why GitHub's repository metadata
API reports `"license": null` for this repo — GitHub's license
detector only recognizes top-level `LICENSE`/`LICENSE.md` files, not
license text embedded in a README). The relevant excerpt, fetched
2026-07-22 from
<https://github.com/mnielsen/neural-networks-and-deep-learning/blob/master/README.md>:

> ## License
>
> MIT License
>
> Copyright (c) 2012-2022 Michael Nielsen
>
> Permission is hereby granted, free of charge, to any person obtaining
> a copy of this software and associated documentation files (the
> "Software"), to deal in the Software without restriction, including
> without limitation the rights to use, copy, modify, merge, publish,
> distribute, sublicense, and/or sell copies of the Software, and to
> permit persons to whom the Software is furnished to do so, subject to
> the following conditions:
>
> The above copyright notice and this permission notice shall be
> included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
> EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
> MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
> NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
> LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
> OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
> WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Because the MIT license requires the copyright notice and permission
notice to be included in copies/substantial portions of the software,
the full text above is reproduced verbatim, and this directory's
`README.md` links back to the original repository and its license.
This code MIT license is **independent of** the book's own CC BY-NC
3.0 license (see the root `LICENSE-CONTENT.md`), which governs the
book's prose/equations/images and the verbatim Python 2.7 listings
embedded in `docs/`.

Also worth noting: the original repository's own `README.md` (fetched
2026-07-22) says:

> The code is written for Python 2.6 or 2.7. There is a version for
> Python 3.8-3.10
> [here](https://github.com/unexploredtest/neural-networks-and-deep-learning).
> I will not be updating the current repository for Python 3
> compatibility.
>
> The program `src/network3.py` uses version 0.6 or 0.7 of the Theano
> library. It needs modification for compatibility with later versions
> of the library. I will not be making such modifications.

Nielsen explicitly disclaims maintaining a Python 3 version himself and
points to a community fork; that fork was not vendored here — this
port was done independently, directly from the Python 2.7 originals,
per the P5-1 ticket instructions (minimal mechanical changes only).

## What changed in the port

See the module docstrings in each ported file
(`mnist_loader.py`, `network.py`, `network2.py`, `network3.py`) for the
precise, itemized mechanical changes (xrange -> range, print statements
-> print() calls, cPickle -> pickle with `encoding='latin1'`, zip()
wrapped in list() where the result is shuffled/sliced, integer division
`/` -> `//` in network3.py where the original 2.7 code relied on
integer results). No algorithms, formulas, or program structure were
changed.

`network3.py` additionally carries a large header notice: it targets
Theano's original 0.6/0.7 API verbatim (mechanically ported), Theano
itself being an unmaintained/dead project. It is provided for
reference/reading only and is not expected to run without a working
(and likely patched) Theano install. `network.py`, `network2.py`, and
`mnist_loader.py` are the fully working, tested Python 3 code in this
directory.

## Getting the MNIST data file

None of the ported modules bundle `mnist.pkl.gz` (large binary blob,
not committed to this repository, per the P5-1 ticket instructions).
To run any of the loaders/smoke test, obtain it yourself:

1. From Nielsen's repository directly:
   <https://github.com/mnielsen/neural-networks-and-deep-learning/raw/master/data/mnist.pkl.gz>
   (or `git clone` the repo and copy `data/mnist.pkl.gz`).
2. Place it at `code/python3/data/mnist.pkl.gz` in this repo (the
   `data/` subdirectory here is gitignored/empty on purpose), **or**
   set the `MNIST_DATA_PATH` environment variable to wherever you put
   it, **or** pass an explicit `path=` argument to
   `mnist_loader.load_data()` / `load_data_wrapper()` /
   `network3.load_data_shared()`.

This data file is itself a repackaging of the MNIST database (LeCun,
Cortes, Burges), distributed by Nielsen's repository under the same
MIT license as its code.
