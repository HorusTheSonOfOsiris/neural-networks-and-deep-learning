# Neural Networks and Deep Learning — unofficial readable mirror

This repository is an **unofficial, non-commercial static-site reformatting**
of [*Neural Networks and Deep Learning*](http://neuralnetworksanddeeplearning.com)
by **Michael Nielsen**, built with [MkDocs](https://www.mkdocs.org/) and
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). The goal
is a more comfortable reading experience (typography, light/dark mode,
search, working equation anchors) on top of the original text — verbatim,
not paraphrased.

## Attribution & license

- Original work: © Michael Nielsen — <http://neuralnetworksanddeeplearning.com>
- License: [Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0)](https://creativecommons.org/licenses/by-nc/3.0/deed.en)
- This is an **unofficial** reformatting for readability, distributed
  **non-commercially**, with no ads, no monetized analytics, and no paid
  access. It is not affiliated with or endorsed by Michael Nielsen.
- Book content in this repository (everything under `docs/` derived from the
  original book, plus `raw/`) remains under CC BY-NC 3.0 — see
  [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md).
- The tooling in this repository (`tools/`, `mkdocs.yml`, `docs/css/`,
  `docs/js/`, and other site infrastructure written for this project) is
  separately licensed MIT — see [`LICENSE`](LICENSE). The MIT license does
  **not** apply to the book text, equations, code samples, or images
  reproduced from the original source.

## Status

The readable MVP is complete: all six chapters, the appendix, exercises,
acknowledgements, and FAQ have been converted from committed source snapshots.
Automated verification covers equations and anchors, sidenotes, internal links,
images, interactive fallbacks, and byte-faithful Python 2.7 code blocks. Paper
styling, local MathJax vendoring, visual review, and interactive widget ports
remain in progress; see `PENDING.md` for the current work list.

## How to build

Requires Python 3.13+.

### With `uv` (recommended)

```bash
uv sync
uv run pytest tools/test_convert.py tools/test_verify.py -q
uv run python tools/verify.py     # source-fidelity checks + strict test build
uv run mkdocs serve      # live-reload dev server at http://127.0.0.1:8000
uv run mkdocs build --strict   # production build, fails on any warning
```

### With `pip`

```bash
pip install -e .
python tools/verify.py
mkdocs serve
mkdocs build --strict
```

The built site is written to `site/` (git-ignored) and is deployed to
GitHub Pages via `.github/workflows/deploy.yml` on push to `main`.

## Repository layout

See `Plan.md` §2 for the authoritative layout. In short:

- `tools/` — scraping/conversion/verification scripts (Python).
- `raw/` — committed raw HTML snapshots of the source site (input of record).
- `docs/` — the MkDocs source (Markdown pages, images, CSS, JS).
- `mkdocs.yml` — site configuration (Material theme, MathJax, extensions).

## Disclaimer

This is a non-commercial, unofficial fan reformatting intended to improve
readability of a freely available online book. All credit for the original
content belongs to Michael Nielsen. If you are the rights holder and have
concerns about this repository, please open an issue.
