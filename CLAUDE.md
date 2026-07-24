# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# DOs

- Always use brainstorming skill to brainstorm things.
- Use cheaper agents like Haiku to discover and read files.
- Use Sonnet to do the implement.
- Ask questions to fable if stuck.
- Check for the pattern.
- Try and save tokens as much as possible.

# What this repo is

Unofficial, non-commercial static-site mirror of Michael Nielsen's _Neural
Networks and Deep Learning_, rebuilt with MkDocs + the `mkdocs-shadcn` theme for
a better reading experience (paper typography, light/dark, search, equation
anchors, interactive figures). Book text is verbatim, not paraphrased, and stays
under CC BY-NC 3.0; the tooling/site infra is MIT (see `README.md` for the split).

# Commands

Requires Python 3.13+. `uv` is the primary workflow (`pip install -e .` also works).

```bash
uv sync
uv run mkdocs serve                 # live-reload dev server at http://127.0.0.1:8000
uv run mkdocs build --strict        # production build to site/ (fails on any warning)
uv run python tools/verify.py       # source-fidelity checks + strict test build
uv run pytest tools/test_convert.py tools/test_verify.py -q   # unit tests
uv run pytest tools/test_verify.py::test_name -q              # single test
```

`site/` is git-ignored; GitHub Pages deploys it via `.github/workflows/deploy.yml` on push to `main`.

# Architecture

**Conversion pipeline — `raw/` is the input of record, `docs/` is generated.**
`raw/*.html` are committed snapshots of the original site. `tools/convert.py` is a
_targeted_ HTML→Markdown converter (deliberately NOT a generic pandoc/html2md
pass — it handles this book's specific equation, sidenote, and code-block
markup). `tools/scrape.py` fetches sources; `tools/verify.py` compares every
generated `docs/chapN.md` back against its `raw/` snapshot and fails on drift in
equations/anchors, sidenotes, internal links, images, interactive fallbacks, and
byte-faithful Python 2.7 code blocks. **When editing `docs/*.md` book content,
keep `tools/verify.py` passing** — the raw HTML is authoritative.

**Rendering — theme + overrides + one stylesheet.** `mkdocs.yml` uses the
`shadcn` theme with `custom_dir: overrides` (`overrides/templates/page.html`,
`extra_head.html`). Essentially all visual styling lives in the single
`docs/css/paper.css`; the `pygments_style` in `mkdocs.yml` only sets code-token
colors. Every book page carries `class="typography"`, so page CSS is scoped
under `.typography`.

**Math — arithmatex (generic) + locally vendored MathJax.** Markdown `$...$` /
`$$...$$` is rewritten by `pymdownx.arithmatex` into `arithmatex`-classed spans.
`docs/js/mathjax-config.js` restricts MathJax to `processHtmlClass` — so any
hand-authored raw-HTML math (e.g. `<div class="math-display">` eqnarray blocks)
must have its class listed there or it renders as raw LaTeX. MathJax itself is
vendored under `docs/js/mathjax/` (no CDN). Load order matters: config loads
before the MathJax script (see `extra_javascript` in `mkdocs.yml`).

**Interactive figures.** Original static book figures are replaced by per-chapter
vanilla-JS modules in `docs/js/interactives/` (`chapN-*.js`), wired in via
`extra_javascript`. They progressively enhance a static fallback in the Markdown.

Note: scripts and `README.md` reference a `Plan.md` for the authoritative spec
and section numbers, but that file is not committed to the repo.
