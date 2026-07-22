// MathJax 3 configuration for the NNDL static-site mirror.
//
// SOURCE-VALIDATED CORRECTION (Plan.md §6 / §8):
// The original book was authored against MathJax 2.7.1 with
// `equationNumbers: {autoNumber: "AMS"}` plus explicit `\tag{}` calls mixed
// in. Migrating to MathJax 3 naively with `tags: 'none'` strips the numbers
// off every auto-numbered `\begin{eqnarray}` block. We must instead enable
// `tags: 'ams'` AND load the `ams` package so `\tag{n}`, `\nonumber`, and
// `eqnarray` all render exactly as they did in the source.
//
// This file is loaded via extra_javascript BEFORE the MathJax CDN script
// (see mkdocs.yml), which is the required load order for `window.MathJax`
// to be picked up as MathJax's config object.
//
// We use pymdownx.arithmatex with `generic: true` in mkdocs.yml, so this
// config also declares the arithmatex-recommended `ignoreHtmlClass` /
// `processHtmlClass` pair so MathJax only processes elements arithmatex
// tags, not arbitrary page markup.

window.MathJax = {
  tex: {
    // arithmatex (generic loader) normalizes markdown math into \( \) / \[ \]
    // wrapped spans, but we also keep the raw $...$ / $$...$$ delimiters live
    // so hand-authored or convert.py-emitted raw-HTML math (Plan.md §4.2)
    // passes through cleanly even outside an .arithmatex wrapper.
    inlineMath: [
      ["\\(", "\\)"],
      ["$", "$"],
    ],
    displayMath: [
      ["\\[", "\\]"],
      ["$$", "$$"],
    ],
    processEscapes: true,
    processEnvironments: true,
    tags: "ams",
    packages: { "[+]": ["ams"] },
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
