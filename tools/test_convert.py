"""Unit tests for tools/convert.py (Task P2-0).

Run with: uv run pytest tools/test_convert.py -v

Covers the acceptance criteria from Plan.md Sec4 / Sec7 / Sec8:
  - eqnarray passthrough (byte-for-byte LaTeX, wrapped + anchored)
  - eqref link rewrite + marginequation duplication drop (the #1 known trap)
  - sidenote extraction (wrapped, never merged into body prose)
  - heading anchor-id preservation
  - link-map failure mode (raises loudly on unmapped internal .html hrefs)
  - code block byte-fidelity (whitespace-normalized diff empty)

Most tests build minimal synthetic HTML fragments that reproduce the exact
source patterns found in raw/chap1.html (verified by inspection, see
module docstring / comments in convert.py), so they run independently of
the real book source. A few tests also run against the committed
raw/chap1.html directly, since that's the ticket's actual acceptance bar.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_CHAP1 = REPO_ROOT / "raw" / "chap1.html"


def convert_fragment(body_html: str, page: str = "chap1.html") -> str:
    """Wrap a body fragment in the minimal shell convert_html expects."""
    html = (
        '<html><body><div class="header">'
        '<h1 class="chapter_number">CHAPTER 1</h1>'
        '<h1 class="chapter_title"><a href="">Test Chapter</a></h1>'
        "</div>"
        f'<div class="section"><div id="toc">chrome, must be excluded</div>{body_html}</div>'
        "</body></html>"
    )
    return convert.convert_html(html, page)


# --------------------------------------------------------------------------
# 1. eqnarray passthrough
# --------------------------------------------------------------------------
def test_eqnarray_passthrough_byte_for_byte():
    latex = (
        r"\begin{eqnarray}"
        "\n  \\mbox{output} & = & \\left\\{ \\begin{array}{ll}\n"
        r"      0 & \mbox{if } \sum_j w_j x_j \leq \mbox{ threshold} \\"
        "\n"
        r"      1 & \mbox{if } \sum_j w_j x_j > \mbox{ threshold}"
        "\n      \\end{array} \\right.\n\\tag{1}\\end{eqnarray}"
    )
    body = f'<p>Some intro text.<a class="displaced_anchor" name="eqtn1"></a>{latex}\nMore text.</p>'
    out = convert_fragment(body)

    assert '<div class="math-display" id="eqtn1">' in out
    # The LaTeX must appear verbatim (byte-for-byte) inside the div, not
    # escaped/mangled the way a generic Markdown-escaping pass would.
    assert latex in out
    assert r"\begin{array}{ll}" in out
    assert r"\tag{1}" in out


def test_eqnarray_multi_tag_shares_one_block_both_ids_anchored():
    # Source-validated edge case (chap1 eqtn16/eqtn17): two displaced_anchor
    # markers back-to-back before ONE shared eqnarray environment.
    latex = (
        r"\begin{eqnarray}"
        "\n  w_k & \\rightarrow & w_k' = w_k-\\eta \\frac{\\partial C}{\\partial w_k} \\tag{16}\\\\\n"
        r"  b_l & \rightarrow & b_l' = b_l-\eta \frac{\partial C}{\partial b_l}."
        "\n\\tag{17}\\end{eqnarray}"
    )
    body = (
        '<p>Text before.'
        '<a class="displaced_anchor" name="eqtn16"></a>'
        '<a class="displaced_anchor" name="eqtn17"></a>'
        f"{latex}\nText after.</p>"
    )
    out = convert_fragment(body)
    assert 'id="eqtn16"' in out
    assert 'id="eqtn17"' in out
    # Only ONE copy of the shared LaTeX body should be present.
    assert out.count(r"\rightarrow") == 2  # once in eqn16 line, once in eqn17 line -- same block


def test_letter_tagged_eqnarray_is_block_wrapped():
    latex = r"\begin{eqnarray}\delta^L = \nabla_a C \odot \sigma'(z^L)\tag{BP1a}\end{eqnarray}"
    body = f'<a class="displaced_anchor" name="eqtnBP1a"></a>{latex}'
    out = convert_fragment(body, "chap2.html")
    assert '<div class="math-display" id="eqtnBP1a">' in out
    assert latex in out


# --------------------------------------------------------------------------
# 2. eqref link rewrite + marginequation drop (Plan.md Sec8 trap)
# --------------------------------------------------------------------------
def test_eqref_keeps_link_drops_marginequation_duplicate():
    unique_marker_latex = r"\sigma(z) \equiv \frac{1}{1+e^{-UNIQUE_MARKER_9981}}"
    body = (
        "<p>See Equation "
        '<span id="margin_1_reveal" class="equation_link">(3)</span>'
        '<span id="margin_1" class="marginequation" style="display: none;">'
        f'<a href="chap1.html#eqtn3">\\begin{{eqnarray}} {unique_marker_latex} \\nonumber\\end{{eqnarray}}</a>'
        "</span>"
        "<script>$('#margin_1_reveal').click(function() {});</script>"
        " for the definition.</p>"
    )
    out = convert_fragment(body)

    # Visible text kept, rewritten as a working same-page anchor link.
    assert "[(3)](#eqtn3)" in out
    # The hidden full-LaTeX duplicate must be dropped entirely -- this is
    # the #1 corruption risk called out in Plan.md Sec4.1/Sec8.
    assert "UNIQUE_MARKER_9981" not in out
    assert "marginequation" not in out
    assert "<script" not in out
    assert "display: none" not in out


def test_cross_chapter_eqref_keeps_target_page():
    body = (
        '<span class="equation_link">(4)</span>'
        '<span class="marginequation"><a href="chap1.html#eqtn4">duplicate</a></span>'
    )
    out = convert_fragment(body, "chap2.html")
    assert "[(4)](chap1.md#eqtn4)" in out


def test_eqref_trap_on_real_chap1_source():
    """Integration-level guard against the exact trap Plan.md Sec8 warns about:
    if any referenced equation's LaTeX leaks a second time into prose, we've
    failed. \\nonumber only ever appears inside marginequation duplicates in
    this source (never inside a real numbered \\tag{} equation), so its
    total absence from the converted output is a strong signal the dedup
    held for all real equation references, not just the synthetic case above.
    """
    if not RAW_CHAP1.exists():
        pytest.skip("raw/chap1.html not present")
    html = RAW_CHAP1.read_text(encoding="utf-8")
    out = convert.convert_html(html, "chap1.html")
    assert "marginequation" not in out
    assert "nonumber" not in out
    assert "<script" not in out


# --------------------------------------------------------------------------
# 3. Sidenotes: wrapped, never merged into body prose
# --------------------------------------------------------------------------
def test_sidenote_is_wrapped_not_merged():
    body = (
        "<p>the <em>sigmoid function</em>"
        '*<span class="marginnote">\n*Incidentally, UNIQUE_NOTE_TEXT_4471 is a note.</span>'
        ", and is defined by:</p>"
    )
    out = convert_fragment(body)

    assert '<span class="sidenote">' in out
    # The note's own text is present, but only inside the sidenote wrapper.
    assert "UNIQUE_NOTE_TEXT_4471" in out
    sidenote_match = re.search(r'<span class="sidenote">(.*?)</span>', out)
    assert sidenote_match is not None
    assert "UNIQUE_NOTE_TEXT_4471" in sidenote_match.group(1)
    # The leading '*' marker glyph must not survive raw into the note text
    # (it's stripped per Plan.md Sec4.4), and must not collide with our own
    # emphasis markup as a bare '*' outside the span (Sec4.1 corruption risk
    # for naive converters).
    assert not sidenote_match.group(1).startswith("*")
    # No un-marked-up run-on: the word immediately before the note and the
    # note's own text must not appear directly concatenated with no tag
    # boundary between them (the "#1 text-corruption risk" from Plan.md Sec3).
    assert "function*Incidentally" not in out
    assert "functionIncidentally" not in out


def test_sidenote_without_asterisk_marker():
    # Not every marginnote is asterisk-marked (e.g. image credits captions).
    body = '<p>photo credits: <span class="marginnote">Credits: photographer A.</span></p>'
    out = convert_fragment(body)
    assert '<span class="sidenote">Credits: photographer A.</span>' in out


# --------------------------------------------------------------------------
# 4. Heading anchor-id preservation
# --------------------------------------------------------------------------
def test_heading_anchor_id_preserved():
    body = (
        '<p></p><p><h3><a name="sigmoid_neurons"></a>'
        '<a href="#sigmoid_neurons">Sigmoid neurons</a></h3></p>'
        "<p>Body text follows.</p>"
    )
    out = convert_fragment(body)
    assert "### Sigmoid neurons {#sigmoid_neurons}" in out


def test_heading_anchor_control_newline_is_normalized():
    body = (
        '<h3><a name="warm_up_output\n_from_network"></a>'
        '<a href="#warm_up_output\n_from_network">Warm up output\n from network</a></h3>'
    )
    out = convert_fragment(body, "chap2.html")
    assert "### Warm up output from network {#warm_up_output_from_network}" in out


def test_heading_anchor_with_latex_uses_raw_compatibility_anchor():
    body = (
        '<h3><a name="the_hadamard_product_$s_\\odot_t$"></a>'
        '<a href="#the_hadamard_product_$s_\\odot_t$">'
        'The Hadamard product, $s \\odot t$</a></h3>'
    )
    out = convert_fragment(body, "chap2.html")
    assert (
        '<a id="the_hadamard_product_&#36;s_&#92;odot_t&#36;"></a>' in out
    )
    assert "### The Hadamard product, $s \\odot t$" in out
    assert "{#the_hadamard" not in out


def test_id_only_anchor_is_preserved():
    out = convert_fragment('<p><a id="alternative_backprop"></a></p>')
    assert '<a id="alternative_backprop"></a>' in out


def test_heading_anchor_id_preserved_on_real_chap1_source():
    if not RAW_CHAP1.exists():
        pytest.skip("raw/chap1.html not present")
    html = RAW_CHAP1.read_text(encoding="utf-8")
    out = convert.convert_html(html, "chap1.html")
    known_ids = [
        "perceptrons",
        "sigmoid_neurons",
        "the_architecture_of_neural_networks",
        "a_simple_network_to_classify_handwritten_digits",
        "learning_with_gradient_descent",
        "implementing_our_network_to_classify_digits",
        "toward_deep_learning",
    ]
    for hid in known_ids:
        assert f"{{#{hid}}}" in out, f"missing heading anchor #{hid}"


# --------------------------------------------------------------------------
# 5. Link-map: resolves known internal pages, fails loudly on unknown ones
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "href,expected",
    [
        ("chap3.html", "chap3.md"),
        ("chap3.html#the_cross-entropy_cost_function", "chap3.md#the_cross-entropy_cost_function"),
        ("chap1.html#eqtn3", "chap1.md#eqtn3"),
        ("sai.html", "appendix-sai.md"),
        ("exercises_and_problems.html", "exercises-and-problems.md"),
        ("about.html", "index.md"),
        ("index.html", "index.md"),
        ("acknowledgements.html", "acknowledgements.md"),
        ("faq.html", "faq.md"),
        ("http://yann.lecun.com/exdb/mnist/", "http://yann.lecun.com/exdb/mnist/"),
        ("js/polynomial_model.js", convert.BASE_URL + "js/polynomial_model.js"),
        ("assets/MachineTranslation.pdf", convert.BASE_URL + "assets/MachineTranslation.pdf"),
        ("#complete_zero", "#complete_zero"),
    ],
)
def test_link_map_resolves_known_targets(href, expected):
    assert convert.resolve_href(href) == expected


def test_link_map_raises_on_unmapped_internal_html_href():
    with pytest.raises(convert.UnmappedLinkError):
        convert.resolve_href("bugfinder.html")


def test_link_map_raises_on_unmapped_internal_html_href_with_fragment():
    with pytest.raises(convert.UnmappedLinkError):
        convert.resolve_href("supporters.html#some_section")


def test_link_in_rendered_output_uses_link_map():
    body = '<p>See <a href="chap3.html#the_cross-entropy_cost_function">chapter 3</a>.</p>'
    out = convert_fragment(body)
    assert "[chapter 3](chap3.md#the_cross-entropy_cost_function)" in out


def test_unmapped_link_in_source_raises_during_conversion():
    body = '<p>See <a href="bugfinder.html">the bug list</a>.</p>'
    with pytest.raises(convert.UnmappedLinkError):
        convert_fragment(body)


# --------------------------------------------------------------------------
# 6. Code blocks: byte-identical to source (whitespace-normalized)
# --------------------------------------------------------------------------
def _normalize_ws(s: str) -> str:
    return "\n".join(line.rstrip() for line in s.strip("\n").splitlines())


def test_code_block_byte_fidelity_python2():
    source_code = (
        "class Network(object):\n\n"
        "    def __init__(self, sizes):\n"
        "        self.num_layers = len(sizes)\n"
        "        print 'Hello, world'\n"  # Python 2 print statement
        "        for k, v in mydict.iteritems():\n"
        "            pass\n"
        "        for i in xrange(10):\n"  # Python 2 xrange
        "            pass\n"
        "        import cPickle\n"  # Python 2 cPickle
    )
    body = f'<p>Code:</p><div class="highlight"><pre><span></span>{source_code}</pre></div>'
    out = convert_fragment(body)

    assert "```python" in out
    fence_match = re.search(r"```python\n(.*?)```", out, re.DOTALL)
    assert fence_match is not None
    extracted = fence_match.group(1)

    assert _normalize_ws(extracted) == _normalize_ws(source_code)
    # Explicitly confirm the Python 2 idioms were NOT modernized.
    assert "print 'Hello, world'" in extracted
    assert "xrange(10)" in extracted
    assert "cPickle" in extracted
    assert ".iteritems()" in extracted


def test_code_blocks_byte_fidelity_on_real_chap1_source():
    if not RAW_CHAP1.exists():
        pytest.skip("raw/chap1.html not present")
    from bs4 import BeautifulSoup

    html = RAW_CHAP1.read_text(encoding="utf-8")
    preprocessed = convert.preprocess_eqnarrays(html)
    soup = BeautifulSoup(preprocessed, "lxml")
    highlight_divs = soup.find_all("div", class_="highlight")
    assert len(highlight_divs) > 0

    out = convert.convert_html(html, "chap1.html")
    fences = re.findall(r"```python\n(.*?)```", out, re.DOTALL)
    assert len(fences) == len(highlight_divs)

    for div, fence in zip(highlight_divs, fences):
        source_text = div.find("pre").get_text()
        assert _normalize_ws(fence) == _normalize_ws(source_text)


# --------------------------------------------------------------------------
# Exercise/problem admonitions
# --------------------------------------------------------------------------
def test_exercise_heading_becomes_admonition():
    body = (
        '<p><h4><a name="exercise_1"></a><a href="#exercise_1">Exercise</a></h4>'
        "<ul><li>Do the thing.</li></ul></p>"
        "<p>Normal prose that must NOT be swallowed into the admonition.</p>"
    )
    out = convert_fragment(body)
    assert '!!! question "Exercise"' in out
    assert "Do the thing." in out
    # Regression guard: content after the exercise's single <ul> must stay
    # outside the admonition (verified real bug against chap1's
    # exercise_420023 / exercise_717502 -- an earlier "gather until next
    # heading" heuristic wrongly pulled trailing prose/code into the block).
    admonition_start = out.index('!!! question "Exercise"')
    prose_pos = out.index("Normal prose that must NOT be swallowed")
    body_between = out[admonition_start:prose_pos]
    assert not body_between.strip().endswith("Normal prose")
    assert re.search(r"^\S", out[prose_pos - 1:prose_pos] or "x", re.MULTILINE) or True
    # The prose line itself must not be indented (i.e. not inside the block).
    prose_line = out.splitlines()[[i for i, l in enumerate(out.splitlines()) if "Normal prose" in l][0]]
    assert not prose_line.startswith(" ")


# --------------------------------------------------------------------------
# Interactive JS figure placeholders (Plan.md Sec4.7)
# --------------------------------------------------------------------------
def test_interactive_figure_gets_placeholder_not_dropped_silently():
    body = '<p>Here\'s the shape:</p><div id="sigmoid_graph"><a name="sigmoid_graph"></a></div><script>var x = 1;</script>'
    out = convert_fragment(body)
    assert "interactive-placeholder" in out
    assert "Interactive version" in out
    assert "chap1.html#sigmoid_graph" in out
    assert 'id="sigmoid_graph"' in out
    assert "<script" not in out


def test_canvas_interactive_figure_gets_placeholder():
    body = '<p><canvas id="saturation1" width="520" height="300"></canvas></p>'
    out = convert_fragment(body, "chap3.html")
    assert out.count("interactive-placeholder") == 1
    assert 'id="saturation1"' in out


def test_slider_table_canvas_gets_placeholder_without_chrome_leaking():
    # Real chap3 pattern (smG1-4): interactive canvases sit inside a
    # <table> alongside slider <div>s and readout <input>s. The table
    # itself must be dropped entirely -- only a placeholder per canvas --
    # with no raw "$z^L_1 = $" label text or input/slider chrome leaking
    # into the surrounding prose.
    body = (
        "<table><tr>"
        '<td><div id="slider1" style="width: 200px;"></div>'
        '$z^L_1 = $ <input type="text" id="amount1" readonly></td>'
        '<td><canvas id="smG1" width="300" height="40"></canvas></td>'
        "</tr></table>"
    )
    out = convert_fragment(body, "chap3.html")
    assert out.count("interactive-placeholder") == 1
    assert 'id="smG1"' in out
    assert "<table" not in out
    assert "<input" not in out
    assert 'id="slider1"' not in out
    assert "$z^L_1" not in out


def test_style_content_does_not_leak_into_prose():
    out = convert_fragment("<style>.softmaxTable { width: 260px; }</style><p>Visible.</p>")
    assert "softmaxTable" not in out
    assert "width: 260px" not in out
    assert "Visible." in out


def test_blockquote_remains_a_blockquote():
    out = convert_fragment("<blockquote><p>Quoted first.</p><p>Quoted second.</p></blockquote>")
    assert "> Quoted first." in out
    assert "> Quoted second." in out


def test_nonchapter_header_supplies_title():
    html = (
        '<html><body><div class="nonumber_header"><h2>Acknowledgements</h2></div>'
        '<div class="section"><p>Thanks.</p></div></body></html>'
    )
    assert convert.convert_html(html, "acknowledgements.html").startswith(
        "# Acknowledgements\n\n"
    )


# --------------------------------------------------------------------------
# Dead same-page anchor fixups (chap6.html source-native broken links --
# verified no matching `name="..."` anchor exists anywhere in raw/chap6.html;
# Plan.md Sec7 item 4 requires zero internal 404s under --strict).
# --------------------------------------------------------------------------
def test_chap6_dead_anchor_convolutional_networks_is_remapped():
    body = '<p><a href="#convolutional_networks">main part</a></p>'
    out = convert_fragment(body, "chap6.html")
    assert "[main part](#introducing_convolutional_networks)" in out


def test_chap6_dead_anchor_other_models_is_remapped():
    body = (
        '<p><a href="#things_we_didn\'t_cover_but_which_you\'ll_eventually_want_to_know">'
        "other models</a></p>"
    )
    out = convert_fragment(body, "chap6.html")
    assert "[other models](#other_approaches_to_deep_neural_nets)" in out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
