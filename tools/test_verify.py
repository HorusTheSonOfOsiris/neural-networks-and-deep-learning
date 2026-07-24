"""Focused regression tests for tools/verify.py."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify  # noqa: E402


SOURCE = r"""
<html><body><div class="section"><div id="toc"><img src="images/arrow.png"></div>
<h3><a name="section_one"></a><a href="#section_one">Section one</a></h3>
<p><a class="displaced_anchor" name="eqtn1"></a>
\begin{eqnarray}x & = & 1.\tag{1}\end{eqnarray}</p>
<p>Text*<span class="marginnote">*A note.</span></p>
<p><img src="images/example.png"></p>
<div class="highlight"><pre>print 'Python 2'\n</pre></div>
</div></body></html>
"""

OUTPUT = r"""# Test

### Section one {#section_one}

<div class="math-display" id="eqtn1">
\begin{eqnarray}x & = & 1.\tag{1}\end{eqnarray}
</div>

Text<sup>&#42;</sup><span class="sidenote">A note.</span>

<img src="../images/example.png" alt="">

```python
print 'Python 2'\n
```

<div class="interactive-placeholder" id="widget">
<p><em>Interactive version on the <a href="http://example.test/#widget">original site</a>.</em></p>
</div>
"""


def failure_checks(output: str, interactives: set[str] | None = None) -> set[int]:
    failures, _ = verify.verify_chapter_content(
        "chap1.html", SOURCE, output, interactives or {"widget"}
    )
    return {failure.check for failure in failures}


def test_valid_chapter_passes_checks_1_3_5_6():
    failures, stats = verify.verify_chapter_content(
        "chap1.html", SOURCE, OUTPUT, {"widget"}
    )
    assert failures == []
    assert stats.equations == 1
    assert stats.interactives == 1


def test_math_and_leakage_regressions_fail():
    broken = OUTPUT.replace('<div class="math-display" id="eqtn1">', "")
    broken += "\n<script>bad()</script>\n"
    checks = failure_checks(broken)
    assert 1 in checks
    assert 2 in checks


def test_image_placeholder_and_code_regressions_fail():
    broken = OUTPUT.replace("images/example.png", "images/wrong.png")
    broken = broken.replace('id="widget"', 'id="wrong-widget"')
    broken = broken.replace("print 'Python 2'", "print('modernized')")
    checks = failure_checks(broken)
    assert {5, 6}.issubset(checks)


def test_local_link_checker_rejects_missing_fragment(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "one.md").write_text("[broken](two.md#missing)\n", encoding="utf-8")
    (docs / "two.md").write_text("# Present {#present}\n", encoding="utf-8")
    failures = verify.verify_local_links(docs)
    assert any("anchor target does not exist" in failure.message for failure in failures)


def test_image_checker_resolves_urls_from_built_page_directory(
    tmp_path: Path, monkeypatch
):
    docs = tmp_path / "docs"
    images = docs / "images"
    images.mkdir(parents=True)
    (images / "example.png").write_bytes(b"image")
    (docs / "chap1.md").write_text(
        '<img src="../images/example.png" alt="">\n', encoding="utf-8"
    )
    monkeypatch.setattr(verify, "CHAPTERS", ("chap1",))

    assert verify.verify_image_files(docs) == []
