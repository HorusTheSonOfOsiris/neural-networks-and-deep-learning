#!/usr/bin/env python3
"""convert.py -- targeted HTML -> Markdown converter for the NNDL book.

Per Plan.md Sec4: this is NOT a generic html2md/pandoc pass. The source HTML
(neuralnetworksanddeeplearning.com, Michael Nielsen) has several
source-specific quirks that generic converters mangle:

  * Display math (`\\begin{eqnarray}...\\end{eqnarray}`) sits as *bare text*
    in the DOM, immediately preceded by an `<a class="displaced_anchor"
    name="eqtnN">` marker -- not inside any wrapping element.
  * Equation references (`Equation (3)`) render as a visible
    `<span class="equation_link">` IMMEDIATELY followed by a hidden sibling
    `<span class="marginequation" style="display:none">` containing a FULL
    COPY of the referenced equation's LaTeX. Naive text extraction
    duplicates every referenced equation into the surrounding paragraph.
  * Sidenotes (`<span class="marginnote">`, text starts with a literal `*`)
    are inline in the DOM and must NOT be merged into body prose.
  * The source HTML itself is malformed: `<p>` tags are opened/closed
    inconsistently, so block-level content (`<center>`, embedded `<div>`s)
    routinely splits what is logically one paragraph into a lxml-flattened
    sequence of top-level siblings under `div.section`. This module handles
    that by walking the flattened child stream and re-assembling logical
    paragraphs, rather than trusting `<p>` boundaries alone.

See Plan.md Sec3, Sec4, Sec7, Sec8 for the full spec this file implements.
"""

from __future__ import annotations

from functools import lru_cache
import html as html_lib
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "raw"
DOCS_DIR = REPO_ROOT / "docs"
INVENTORY_PATH = RAW_DIR / "INTERACTIVE_INVENTORY.md"

BASE_URL = "http://neuralnetworksanddeeplearning.com/"

# --------------------------------------------------------------------------
# Plan.md Sec4.5: link map. FAIL LOUDLY on any unmapped internal .html href.
# --------------------------------------------------------------------------
LINK_MAP = {
    "index.html": "index.md",
    "about.html": "index.md",
    "exercises_and_problems.html": "exercises-and-problems.md",
    "chap1.html": "chap1.md",
    "chap2.html": "chap2.md",
    "chap3.html": "chap3.md",
    "chap4.html": "chap4.md",
    "chap5.html": "chap5.md",
    "chap6.html": "chap6.md",
    "sai.html": "appendix-sai.md",
    "acknowledgements.html": "acknowledgements.md",
    "faq.html": "faq.md",
}

EXERCISE_HEADING_WORDS = {"exercise", "exercises", "problem", "problems"}

SIDEBAR_TITLES = {
    "chap1.html": "01 · Handwritten digits",
    "chap2.html": "02 · Backpropagation",
    "chap3.html": "03 · Learning techniques",
    "chap4.html": "04 · Universal approximation",
    "chap5.html": "05 · Deep-network training",
    "chap6.html": "06 · Deep learning",
    "sai.html": "Appendix · Intelligence",
}

_INTERNAL_HTML_RE = re.compile(r"^([\w.-]+\.html)(#.*)?$")

# --------------------------------------------------------------------------
# Pre-existing dead same-page anchors in the *original* source itself
# (verified: no `name="..."` anchor with these ids exists anywhere in
# raw/chap6.html -- this is not a converter defect, the live site has the
# same broken in-page links). Plan.md Sec7 item 4 requires zero internal
# 404s under `mkdocs build --strict`, so these are remapped to the anchor
# the surrounding prose clearly intends (verified by reading the section
# each link's sentence introduces). Link text is left untouched -- only
# the destination fragment changes, same as the cross-chapter LINK_MAP.
# --------------------------------------------------------------------------
_DEAD_ANCHOR_FIXUPS = {
    ("chap6.html", "#convolutional_networks"): "#introducing_convolutional_networks",
    (
        "chap6.html",
        "#things_we_didn't_cover_but_which_you'll_eventually_want_to_know",
    ): "#other_approaches_to_deep_neural_nets",
}


class UnmappedLinkError(ValueError):
    """Raised when an internal .html href has no entry in LINK_MAP."""


def resolve_href(href: str) -> str:
    """Resolve a source href per Plan.md Sec4.5.

    - external http(s) links: unchanged
    - '#fragment' (same-page): unchanged
    - 'chapN.html[#frag]' etc: rewritten via LINK_MAP, fragment preserved
    - unmapped internal .html hrefs: raise loudly (never silently drop a link)
    """
    if href is None:
        return ""
    # The HTML URL-parsing spec strips all TAB/CR/LF from a URL before use
    # (this source has at least one href that got hard-wrapped across a
    # line inside the quoted attribute, e.g. a literal newline mid-fragment).
    href = re.sub(r"[\t\r\n]", "", href).strip()
    if not href:
        return href
    if href.startswith("#"):
        return href
    if re.match(r"^https?://", href) or href.startswith("mailto:"):
        return href
    # These linked resources belong to the original book but were not part
    # of the locally mirrored image inventory.  Keeping them relative makes
    # MkDocs treat them as missing documentation files (and fail a strict
    # build), while an absolute source link preserves the original target.
    if re.match(r"^(?:js|assets)/", href):
        return BASE_URL + href
    m = _INTERNAL_HTML_RE.match(href)
    if not m:
        # Not a recognized internal-page pattern (e.g. a relative asset
        # link); pass through unchanged rather than guessing.
        return href
    base, frag = m.group(1), m.group(2) or ""
    if base not in LINK_MAP:
        raise UnmappedLinkError(
            f"Unmapped internal link target {href!r} (base={base!r}). "
            f"Add it to LINK_MAP in tools/convert.py."
        )
    return LINK_MAP[base] + frag


# --------------------------------------------------------------------------
# Plan.md Sec3 item 4 / Sec4.7: interactive (JS-rendered) figure inventory.
# Loaded from raw/INTERACTIVE_INVENTORY.md (produced by scrape.py) so figure
# ids are source-validated, not guessed/hardcoded per page.
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def load_interactive_ids(page: str, inventory_path: Path = INVENTORY_PATH) -> set[str]:
    if not inventory_path.exists():
        return set()
    text = inventory_path.read_text(encoding="utf-8")
    section_re = re.compile(r"^### " + re.escape(page) + r"\s*$", re.MULTILINE)
    m = section_re.search(text)
    if not m:
        return set()
    rest = text[m.end():]
    next_section = re.search(r"^### ", rest, re.MULTILINE)
    body = rest[: next_section.start()] if next_section else rest
    return set(re.findall(r"\*\*`#([\w-]+)`\*\*", body))


# --------------------------------------------------------------------------
# Plan.md Sec4.2: display-math preprocessing.
#
# The source has 43 `\begin{eqnarray}` blocks in chap1: 22 are real numbered
# display equations (preceded by `<a class="displaced_anchor" name="eqtnN">`
# and containing `\tag{n}`), the rest are the *hidden duplicate copies*
# inside `span.marginequation` (Sec8 trap -- those are dropped entirely,
# never wrapped, never rendered).
#
# We fold each *numbered* eqnarray (plus its displaced_anchor) into a real
# `<div class="math-display" id="eqtnN">` element by regex substitution on
# the raw HTML text, BEFORE parsing with BeautifulSoup. This does two
# things generic HTML parsing can't do on its own here: (1) it makes the
# equation a proper block-level DOM node (breaking any run-on paragraph
# the same way `<center>` does), and (2) it captures the eqtnN id in one
# place instead of hacking sibling-text-node lookahead during rendering.
#
# One real wrinkle found by inspection: some eqnarray blocks carry *two*
# `\tag{}`s and *two* preceding displaced_anchor markers (aligned systems
# of equations sharing one environment, e.g. eqtn16+eqtn17 in chap1). Both
# ids must remain valid link targets, so the second+ id is stored as
# `data-extra-ids` and re-emitted as an empty `<a id="...">` at render time.
# --------------------------------------------------------------------------
_EQNARRAY_RE = re.compile(
    r'((?:<a class="displaced_anchor" name="eqtn[A-Za-z0-9]+"></a>)+)'
    r"\s*"
    r"(\\begin\{eqnarray\}.*?\\end\{eqnarray\})",
    re.DOTALL,
)
_ANCHOR_NAME_RE = re.compile(r'name="(eqtn[A-Za-z0-9]+)"')


def normalize_anchor_id(value: str) -> str:
    """Apply the browser URL normalization relevant to source anchors."""
    return re.sub(r"[\t\r\n]", "", value).strip()


def preprocess_eqnarrays(html: str) -> str:
    def repl(m: re.Match) -> str:
        anchors_blob, body = m.group(1), m.group(2)
        ids = _ANCHOR_NAME_RE.findall(anchors_blob)
        primary, extra = ids[0], ids[1:]
        extra_attr = f' data-extra-ids="{",".join(extra)}"' if extra else ""
        return f'<div class="math-display" id="{primary}"{extra_attr}>{body}</div>'

    return _EQNARRAY_RE.sub(repl, html)


# --------------------------------------------------------------------------
# Inline rendering: converts a sequence of sibling nodes (Tag/NavigableString)
# into one run of inline Markdown/raw-HTML text. Index-based (not purely
# recursive) so the equation_link -> marginequation -> script lookahead
# (Sec4.2/Sec8 eqref trap) can consume/skip siblings explicitly.
# --------------------------------------------------------------------------
def _classes(tag: Tag) -> list[str]:
    return tag.get("class") or []


def render_inline_sequence(nodes: list, current_page: str) -> str:
    parts: list[str] = []
    i = 0
    n = len(nodes)
    while i < n:
        node = nodes[i]
        if isinstance(node, NavigableString):
            parts.append(str(node))
            i += 1
            continue
        if not isinstance(node, Tag):
            i += 1
            continue

        name = node.name
        cls = _classes(node)

        if name in ("script", "style"):
            i += 1
            continue

        fig_id = node.get("id")
        if fig_id and fig_id in load_interactive_ids(current_page):
            parts.append(render_interactive_placeholder(fig_id, current_page))
            i += 1
            continue

        if name == "span" and "marginequation" in cls:
            # Sec8 trap: a lone marginequation not consumed by the
            # equation_link branch below (defensive; should not happen in
            # well-formed source). Drop it -- never surface duplicate LaTeX.
            i += 1
            continue

        if name == "span" and "marginnote" in cls:
            # The body text immediately preceding a marginnote carries a
            # literal '*' marker glyph (source convention). Left as a bare
            # '*', it collides with Markdown emphasis syntax -- e.g. "*foo*"
            # (our own <em> rendering) followed by that literal '*' reads
            # as "*foo**", which Markdown parses as bold, not two separate
            # things. Pull that trailing '*' out of the preceding text and
            # re-emit it as an unambiguous raw <sup>*</sup> marker instead.
            has_marker = False
            if parts and isinstance(parts[-1], str):
                prev = parts[-1]
                m = re.search(r"\*(\s*)$", prev)
                if m:
                    parts[-1] = prev[: m.start()] + m.group(1)
                    has_marker = True
            parts.append(render_sidenote(node, current_page, has_marker))
            i += 1
            continue

        if name == "span" and "equation_link" in cls:
            visible = node.get_text().strip()
            eqtn_href = None
            j = i + 1
            while j < n:
                nd = nodes[j]
                if isinstance(nd, NavigableString) and not str(nd).strip():
                    j += 1
                    continue
                if isinstance(nd, Tag) and nd.name == "span" and "marginequation" in _classes(nd):
                    inner_a = nd.find("a", href=True)
                    if inner_a:
                        raw_href = re.sub(r"[\t\r\n]", "", inner_a["href"]).strip()
                        m = re.search(r"#(eqtn[A-Za-z0-9]+)", raw_href)
                        if m:
                            current_target = LINK_MAP.get(current_page)
                            resolved = resolve_href(raw_href)
                            if current_target and resolved.startswith(current_target + "#"):
                                eqtn_href = resolved.removeprefix(current_target)
                            else:
                                eqtn_href = resolved
                    j += 1
                    continue
                if isinstance(nd, Tag) and nd.name == "script":
                    j += 1
                    continue
                break
            if eqtn_href:
                parts.append(f"[{visible}]({eqtn_href})")
            else:
                parts.append(visible)
            i = j
            continue

        if name in ("em", "i"):
            inner = render_inline_sequence(list(node.children), current_page).strip()
            parts.append(f"*{inner}*" if inner else "")
            i += 1
            continue

        if name in ("strong", "b"):
            inner = render_inline_sequence(list(node.children), current_page).strip()
            parts.append(f"**{inner}**" if inner else "")
            i += 1
            continue

        if name in ("tt", "code"):
            parts.append(f"`{node.get_text()}`")
            i += 1
            continue

        if name == "br":
            parts.append(" ")
            i += 1
            continue

        if name in ("sup", "sub"):
            inner = render_inline_sequence(list(node.children), current_page)
            parts.append(f"<{name}>{inner}</{name}>")
            i += 1
            continue

        if name == "img":
            parts.append(render_image(node))
            i += 1
            continue

        if name == "a":
            href = node.get("href")
            href = _DEAD_ANCHOR_FIXUPS.get((current_page, href), href)
            anchor_id = node.get("name") or node.get("id")
            if not href and anchor_id:
                anchor_id = normalize_anchor_id(anchor_id)
                inner = render_inline_sequence(list(node.children), current_page)
                parts.append(f'<a id="{anchor_id}"></a>{inner}')
                i += 1
                continue
            inner = render_inline_sequence(list(node.children), current_page).strip()
            if href:
                resolved = resolve_href(href)
                parts.append(f"[{inner}]({resolved})" if inner else f"<{resolved}>")
            else:
                parts.append(inner)
            i += 1
            continue

        # Unrecognized inline-ish wrapper (e.g. plain span, font, small):
        # degrade gracefully by recursing into its children rather than
        # dropping content.
        parts.append(render_inline_sequence(list(node.children), current_page))
        i += 1

    text = "".join(parts)
    # The source HTML hand-wraps prose at arbitrary column widths with
    # inconsistent leading whitespace on continuation lines. Left as-is,
    # embedded newlines are harmless in a plain top-level paragraph (Markdown
    # treats a single '\n' as a space) but corrupt list items/admonition
    # bodies, where Markdown's continuation-line indentation rules can misread
    # a source line-wrap as ending the list item or starting a code block.
    # Collapse every run of whitespace containing a newline down to a single
    # space so each rendered inline run is one flat line.
    text = re.sub(r"[ \t]*\n[ \t\n]*", " ", text)
    return text


def render_sidenote(span_tag: Tag, current_page: str, has_marker: bool) -> str:
    text = render_inline_sequence(list(span_tag.children), current_page).strip()
    if text.startswith("*"):
        text = text[1:].lstrip()
    note_id = span_tag.get("data-sidenote-id")
    if not note_id:
        raise ValueError(f"Sidenote in {current_page} has no generated id")
    plain_class = " sidenote-toggle--plain" if not has_marker else ""
    return (
        f'<input type="checkbox" id="{note_id}" class="sidenote-checkbox">'
        f'<label for="{note_id}" class="sidenote-toggle{plain_class}" '
        f'aria-label="Toggle sidenote">'
        f'<sup class="sidenote-marker" aria-hidden="true">&#42;</sup>'
        f'<span class="sidenote-toggle-text">Note</span>'
        f'</label>'
        f'<span class="sidenote">{text}</span>'
    )


def render_image(img_tag: Tag) -> str:
    src = img_tag.get("src", "")
    fname = src.rsplit("/", 1)[-1]
    attrs = [f'src="{src}"']
    for a in ("width", "height"):
        v = img_tag.get(a)
        if v:
            attrs.append(f'{a}="{v}"')
    if re.match(r"^(tikz|valley)", fname, re.IGNORECASE):
        attrs.append('class="diagram"')
    attrs.append('alt=""')
    return f"<img {' '.join(attrs)}>"


def render_math_display(div_tag: Tag) -> str:
    eq_id = div_tag.get("id", "")
    extra_ids = [x for x in (div_tag.get("data-extra-ids") or "").split(",") if x]
    extra_anchors = "".join(f'<a id="{x}"></a>' for x in extra_ids)
    latex = div_tag.get_text()
    return f'<div class="math-display" id="{eq_id}">{extra_anchors}\n{latex}\n</div>'


def render_interactive_placeholder(fig_id: str, current_page: str) -> str:
    url = f"{BASE_URL}{current_page}#{fig_id}"
    return (
        f'<div class="interactive-placeholder" id="{fig_id}">\n'
        f'<p><em>Interactive version on the <a href="{url}">original site</a>.</em></p>\n'
        "</div>"
    )


def render_code_block(highlight_div: Tag) -> str:
    pre = highlight_div.find("pre")
    code_text = pre.get_text() if pre else ""
    if not code_text.endswith("\n"):
        code_text += "\n"
    return f"```python\n{code_text}```"


def extract_heading_anchor(h_tag: Tag) -> tuple[str | None, str]:
    name_a = h_tag.find("a", attrs={"name": True})
    href_a = h_tag.find("a", href=True)
    hid = normalize_anchor_id(name_a["name"]) if name_a else None
    raw_text = href_a.get_text() if href_a else h_tag.get_text()
    text = " ".join(raw_text.split())
    return hid, text


def render_blockquote(tag: Tag, current_page: str) -> str:
    blocks = render_blocks(list(tag.children), current_page)
    quoted: list[str] = []
    for block_index, block in enumerate(blocks):
        if block_index:
            quoted.append(">")
        quoted.extend("> " + line if line else ">" for line in block.splitlines())
    return "\n".join(quoted)


def render_list(tag: Tag, current_page: str) -> str:
    ordered = tag.name == "ol"
    items = tag.find_all("li", recursive=False)
    lines: list[str] = []
    for idx, li in enumerate(items, start=1):
        blocks = render_blocks(list(li.children), current_page)
        if not blocks:
            continue
        marker = f"{idx}." if ordered else "-"
        first, *rest = blocks
        lines.append(f"{marker} {first}")
        indent = " " * (len(marker) + 1)
        for b in rest:
            for line in b.split("\n"):
                lines.append(f"{indent}{line}" if line.strip() else "")
    return "\n".join(lines)


def render_admonition_body(nodes: list, current_page: str) -> str:
    blocks = render_blocks(nodes, current_page)
    indented_blocks = []
    for b in blocks:
        indented_lines = ["    " + line if line.strip() else "" for line in b.split("\n")]
        indented_blocks.append("\n".join(indented_lines))
    return "\n\n".join(indented_blocks)


# --------------------------------------------------------------------------
# Block-level walker. Operates over a flat list of sibling nodes (the
# lxml-flattened children of div.section, or the children of any container
# encountered along the way). See module docstring for why "flat" is the
# right model for this particular malformed source.
# --------------------------------------------------------------------------
def render_blocks(nodes: list, current_page: str) -> list[str]:
    interactive_ids = load_interactive_ids(current_page)
    out: list[str] = []
    pending: list = []
    i = 0
    n = len(nodes)

    def flush() -> None:
        nonlocal pending
        if pending:
            text = render_inline_sequence(pending, current_page).strip()
            if text:
                out.append(text)
            pending = []

    while i < n:
        node = nodes[i]

        if isinstance(node, NavigableString):
            pending.append(node)
            i += 1
            continue

        if not isinstance(node, Tag):
            i += 1
            continue

        name = node.name
        cls = _classes(node)

        if name in ("script", "style"):
            i += 1
            continue

        if node.get("id") == "toc":
            i += 1
            continue

        if name == "p":
            flush()
            text = render_inline_sequence(list(node.children), current_page).strip()
            if text:
                out.append(text)
            i += 1
            continue

        if name in ("h3", "h4"):
            flush()
            hid, htext = extract_heading_anchor(node)
            is_exercise = name == "h4" and htext.strip().lower() in EXERCISE_HEADING_WORDS
            if is_exercise:
                # Source-validated (checked across chap1-6, Plan.md Sec3
                # item 7): every Exercise/Exercises/Problem/Problems heading
                # is immediately followed by exactly one <ul> holding the
                # item(s); regular body prose resumes right after that list
                # with no heading in between. Consume only that one list --
                # NOT "everything up to the next heading" -- otherwise
                # unrelated prose/code that follows in the same subsection
                # gets swallowed into the admonition (verified bug: this
                # happened for chap1's exercise_420023 and exercise_717502,
                # both of which are followed by ordinary paragraphs/code
                # before the next real heading).
                j = i + 1
                while j < n and isinstance(nodes[j], NavigableString) and not str(nodes[j]).strip():
                    j += 1
                sub = []
                if j < n and isinstance(nodes[j], Tag) and nodes[j].name in ("ul", "ol"):
                    sub = [nodes[j]]
                    j += 1
                body = render_admonition_body(sub, current_page)
                anchor = f'<a id="{hid}"></a>\n' if hid else ""
                out.append(f'{anchor}!!! question "{htext.strip()}"\n\n{body}')
                i = j
                continue
            level = "###" if name == "h3" else "####"
            # Arithmatex runs before attr_list.  A source ID containing
            # literal LaTeX delimiters/backslashes (chap2's Hadamard-product
            # heading) is therefore transformed before attr_list can parse
            # it.  Preserve such unusual IDs with a raw compatibility anchor
            # and let Markdown generate its ordinary heading slug as well.
            if hid and ("$" in hid or "\\" in hid):
                safe_hid = html_lib.escape(hid, quote=True).replace("$", "&#36;")
                safe_hid = safe_hid.replace("\\", "&#92;")
                heading = f'<a id="{safe_hid}"></a>\n{level} {htext}'
            else:
                heading = f"{level} {htext} {{#{hid}}}" if hid else f"{level} {htext}"
            out.append(heading)
            i += 1
            continue

        if name == "div" and "math-display" in cls:
            flush()
            out.append(render_math_display(node))
            i += 1
            continue

        if name == "div" and "highlight" in cls:
            flush()
            out.append(render_code_block(node))
            i += 1
            continue

        if node.get("id") in interactive_ids:
            flush()
            out.append(render_interactive_placeholder(node.get("id"), current_page))
            i += 1
            continue

        if name == "table":
            # Sec4.7/bug1: the only <table> in the whole source (chap3's
            # smG1-4 softmax slider grid) is pure interactive-widget chrome
            # -- slider <div>s, readout <input>s, and bare "$z^L_1 = $"
            # label text that must never leak into prose. If the table
            # hosts one or more interactive canvas/div figures, emit a
            # placeholder per figure (deduped, document order) and drop
            # everything else in the table. A table with no interactive
            # content (none exist in this source, but stay defensive) is
            # recursed into generically instead of silently dropped.
            flush()
            interactive_nodes = [
                t
                for t in node.find_all(["div", "canvas"])
                if t.get("id") in interactive_ids
            ]
            if interactive_nodes:
                seen: set[str] = set()
                for t in interactive_nodes:
                    tid = t.get("id")
                    if tid in seen:
                        continue
                    seen.add(tid)
                    out.append(render_interactive_placeholder(tid, current_page))
            else:
                out.extend(render_blocks(list(node.children), current_page))
            i += 1
            continue

        if name == "blockquote":
            flush()
            rendered = render_blockquote(node, current_page)
            if rendered:
                out.append(rendered)
            i += 1
            continue

        if name in ("ul", "ol"):
            flush()
            rendered = render_list(node, current_page)
            if rendered.strip():
                out.append(rendered)
            i += 1
            continue

        if name == "img":
            flush()
            out.append(render_image(node))
            i += 1
            continue

        if name == "hr":
            flush()
            i += 1
            continue

        if name in ("center", "div"):
            # Generic block container (Sec4/§8: this source routinely
            # splits paragraphs around <center>/<div> figure wrappers).
            # Recurse into its children as more block content.
            flush()
            if node.get("id"):
                out.append(f'<a id="{normalize_anchor_id(node["id"])}"></a>')
            out.extend(render_blocks(list(node.children), current_page))
            i += 1
            continue

        # Fall back to treating anything else (em, strong, a, span, tt,
        # code, br, ...) as inline content accumulating into the current
        # paragraph -- this is what correctly reassembles paragraphs that
        # the malformed source HTML split around block elements.
        pending.append(node)
        i += 1

    flush()
    return out


# --------------------------------------------------------------------------
# Top-level page conversion.
# --------------------------------------------------------------------------
def convert_html(html: str, current_page: str) -> str:
    html = preprocess_eqnarrays(html)
    soup = BeautifulSoup(html, "lxml")

    # Give every source sidenote a stable page-local control id. The ids are
    # generated from source order so repeated conversions are byte-identical,
    # and the renderer can emit a checkbox/label pair without global state.
    page_slug = Path(current_page).stem
    for index, sidenote in enumerate(soup.select("span.marginnote"), start=1):
        sidenote["data-sidenote-id"] = f"sidenote-{page_slug}-{index}"

    header = soup.find("div", class_="header")
    title_text = ""
    if header is not None:
        title_h1 = header.find("h1", class_="chapter_title")
        if title_h1 is not None:
            title_text = " ".join(title_h1.get_text().split())
    if not title_text:
        nonumber_header = soup.find("div", class_="nonumber_header")
        title_h2 = nonumber_header.find("h2") if nonumber_header is not None else None
        if title_h2 is not None:
            title_text = " ".join(title_h2.get_text().split())

    section = soup.find("div", class_="section")
    if section is None:
        raise ValueError(f"No div.section found in {current_page}; cannot convert.")

    children = list(section.children)
    blocks = render_blocks(children, current_page)

    doc_parts = []
    sidebar_title = SIDEBAR_TITLES.get(current_page)
    if sidebar_title:
        doc_parts.append(f'---\nsidebar_title: "{sidebar_title}"\n---')
    if title_text:
        doc_parts.append(f"# {title_text}")
    doc_parts.extend(blocks)
    return "\n\n".join(doc_parts) + "\n"


def convert_file(src: Path, dst: Path, page_name: str) -> str:
    html = src.read_text(encoding="utf-8")
    md = convert_html(html, page_name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(md, encoding="utf-8")
    return md


def main(argv: list[str]) -> int:
    page_name = argv[1] if len(argv) > 1 else "chap1.html"
    src = RAW_DIR / page_name
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 1
    stem = page_name.removesuffix(".html")
    dst_name = LINK_MAP.get(page_name, f"{stem}.md")
    dst = DOCS_DIR / dst_name
    convert_file(src, dst, page_name)
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
