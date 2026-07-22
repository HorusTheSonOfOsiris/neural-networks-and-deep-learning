#!/usr/bin/env python3
"""
scrape.py — P1-2: download raw pages + images from
http://neuralnetworksanddeeplearning.com/ and produce an inventory of
JS-rendered (non-<img>) figures.

Outputs:
  raw/<page>.html                 verbatim page snapshots
  docs/images/<original-name>     images, original case preserved
  raw/ASSET_MANIFEST.json         per-page image references + on-disk facts
  raw/INTERACTIVE_INVENTORY.md    every JS-rendered figure, per page

Idempotent: if a target file already exists on disk, it is NOT
re-downloaded (no network request is made for it) unless --force is
passed. This makes a clean re-run a true no-op with zero HTTP traffic.

Usage:
  uv run python tools/scrape.py [--force] [--delay SECONDS]
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_module
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

BASE_URL = "http://neuralnetworksanddeeplearning.com/"

PAGES = [
    "index.html",
    "about.html",
    "exercises_and_problems.html",
    "chap1.html",
    "chap2.html",
    "chap3.html",
    "chap4.html",
    "chap5.html",
    "chap6.html",
    "sai.html",
    "acknowledgements.html",
    "faq.html",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "raw"
IMAGES_DIR = REPO_ROOT / "docs" / "images"
MANIFEST_PATH = RAW_DIR / "ASSET_MANIFEST.json"
INVENTORY_PATH = RAW_DIR / "INTERACTIVE_INVENTORY.md"

USER_AGENT = (
    "NNDL-Book-Mirror/1.0 "
    "(+non-commercial educational mirror project; "
    "contact: jayantraizada1993@live.com)"
)
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch(session: requests.Session, url: str) -> bytes:
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:  # pragma: no cover
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_exc}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# Step 1: download pages
# --------------------------------------------------------------------------


@dataclass
class PageResult:
    name: str
    path: Path
    downloaded: bool  # True if a network request was made this run
    bytes_len: int
    sha256: str


def download_pages(
    session: requests.Session, force: bool, delay: float
) -> list[PageResult]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results: list[PageResult] = []
    for page in PAGES:
        local_path = RAW_DIR / page
        if local_path.exists() and not force:
            data = local_path.read_bytes()
            results.append(
                PageResult(page, local_path, False, len(data), sha256_bytes(data))
            )
            print(f"  [skip]     {page}  (already present, no network request)")
            continue

        url = urljoin(BASE_URL, page)
        data = fetch(session, url)
        local_path.write_bytes(data)
        results.append(
            PageResult(page, local_path, True, len(data), sha256_bytes(data))
        )
        print(f"  [download] {page}  ({len(data)} bytes)")
        time.sleep(delay)
    return results


# --------------------------------------------------------------------------
# Step 2: extract + download images
# --------------------------------------------------------------------------


@dataclass
class ImageRecord:
    filename: str
    path: str  # relative to repo root
    bytes_len: int
    sha256: str
    case_anomaly: bool
    referenced_by: list[str] = field(default_factory=list)


def extract_image_refs(html_text: str) -> list[str]:
    """Return image filenames (case preserved, in document order) referenced
    via <img src="images/...">. Uses BeautifulSoup so multi-line/odd-attribute
    <img> tags (seen in the source, e.g. src on its own line) are handled
    correctly regardless of formatting."""
    soup = BeautifulSoup(html_text, "lxml")
    refs: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("images/"):
            refs.append(src[len("images/") :])
    return refs


def download_images(
    session: requests.Session,
    pages_html: dict[str, str],
    force: bool,
    delay: float,
) -> tuple[dict[str, ImageRecord], dict[str, list[str]], int, int]:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    page_refs: dict[str, list[str]] = {}
    registry: dict[str, ImageRecord] = {}
    downloaded_count = 0
    skipped_count = 0

    # First pass: collect ordered unique-per-page reference lists.
    for page, html_text in pages_html.items():
        refs = extract_image_refs(html_text)
        # de-dup within a page, preserve first-seen order
        seen = []
        for r in refs:
            if r not in seen:
                seen.append(r)
        page_refs[page] = seen

    # Second pass: download each unique filename once, build registry.
    all_filenames: list[str] = []
    for page, refs in page_refs.items():
        for fname in refs:
            if fname not in all_filenames:
                all_filenames.append(fname)

    lowercase_seen: dict[str, str] = {}  # lowercased -> first original name

    for fname in all_filenames:
        local_path = IMAGES_DIR / fname
        lower = fname.lower()
        if lower in lowercase_seen and lowercase_seen[lower] != fname:
            print(
                f"  [WARN] case-insensitive filename collision: "
                f"'{fname}' vs '{lowercase_seen[lower]}' — verify on a "
                f"case-sensitive filesystem"
            )
        else:
            lowercase_seen[lower] = fname

        if local_path.exists() and not force:
            data = local_path.read_bytes()
            skipped_count += 1
            print(f"  [skip]     images/{fname}  (already present)")
        else:
            url = urljoin(BASE_URL, f"images/{fname}")
            data = fetch(session, url)
            local_path.write_bytes(data)
            downloaded_count += 1
            print(f"  [download] images/{fname}  ({len(data)} bytes)")
            time.sleep(delay)

        registry[fname] = ImageRecord(
            filename=fname,
            path=str(local_path.relative_to(REPO_ROOT)),
            bytes_len=len(data),
            sha256=sha256_bytes(data),
            case_anomaly=(fname != fname.lower()),
        )

    for page, refs in page_refs.items():
        for fname in refs:
            registry[fname].referenced_by.append(page)

    return registry, page_refs, downloaded_count, skipped_count


# --------------------------------------------------------------------------
# Step 3: ASSET_MANIFEST.json
# --------------------------------------------------------------------------


def write_manifest(
    registry: dict[str, ImageRecord], page_refs: dict[str, list[str]]
) -> None:
    case_anomalies = sorted(f for f, r in registry.items() if r.case_anomaly)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_base_url": BASE_URL,
        "total_images": len(registry),
        "pages": {
            page: sorted(refs) for page, refs in sorted(page_refs.items())
        },
        "images": {
            fname: {
                "path": rec.path,
                "bytes": rec.bytes_len,
                "sha256": rec.sha256,
                "case_anomaly": rec.case_anomaly,
                "referenced_by": sorted(set(rec.referenced_by)),
            }
            for fname, rec in sorted(registry.items())
        },
        "case_anomalies": {
            "count": len(case_anomalies),
            "note": (
                "Filenames containing uppercase characters. Original case is "
                "preserved on disk deliberately (source pages reference these "
                "exact strings), but GitHub Pages CI runs on a case-sensitive "
                "Linux filesystem — any convert.py output or hand link that "
                "references a lowercased form of these names will 404. P3 "
                "should grep for these filenames case-sensitively."
            ),
            "files": case_anomalies,
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


# --------------------------------------------------------------------------
# Step 4: INTERACTIVE_INVENTORY.md
# --------------------------------------------------------------------------

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
DIV_ID_RE = re.compile(r'<div\s+[^>]*\bid="([^"]+)"[^>]*>', re.IGNORECASE)
CANVAS_ID_RE = re.compile(r'<canvas\s+[^>]*\bid="([^"]+)"[^>]*>', re.IGNORECASE)
D3_TOKEN_RE = re.compile(r"\bd3\.")
CANVAS_TAG_RE = re.compile(r"<canvas\b", re.IGNORECASE)

# Divs that are structural chrome, never figures.
DIV_ID_EXCLUDE_RE = re.compile(r"^(toc(_|$)|slider\d*$)", re.IGNORECASE)

LOOKAHEAD_CHARS = 900  # how far past a <div id=...> to look for d3. usage
NEAR_SCRIPT_CHARS = 200  # how far past a <div id=...> to look for an adjoining <script>
CONTEXT_CHARS = 500  # how much preceding HTML to mine for a caption quote
NEAR_SCRIPT_RE = re.compile(r"<script\b", re.IGNORECASE)


def _trim_orphaned_block_tail(fragment: str, tag: str) -> str:
    """If `fragment` was sliced starting mid-way through a <script>/<style>
    block (possible when the lookback window is shorter than the block),
    there's a </tag> close with no matching opening <tag> earlier in the
    fragment, and SCRIPT_STYLE_RE can't strip that orphaned half — raw
    CSS/JS text would otherwise leak into the quote. Detect the imbalance
    and drop everything up to (and including) the first orphaned close."""
    opens = len(re.findall(rf"<{tag}\b", fragment, re.IGNORECASE))
    closes = list(re.finditer(rf"</{tag}\s*>", fragment, re.IGNORECASE))
    if len(closes) > opens:
        # the earliest close tag is the orphan's end boundary
        return fragment[closes[0].end() :]
    return fragment


def clean_text(raw_html_fragment: str) -> str:
    for tag in ("script", "style"):
        raw_html_fragment = _trim_orphaned_block_tail(raw_html_fragment, tag)

    text = SCRIPT_STYLE_RE.sub(" ", raw_html_fragment)
    text = TAG_RE.sub(" ", text)
    text = html_module.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def quote_context(full_html: str, position: int) -> str:
    """Best-effort short quote of the prose immediately preceding a figure,
    trimmed to the last sentence-ish chunk. This is read directly from the
    page, never invented. Widens the lookback window if the nearby text is
    too thin (e.g. a figure sitting inside a repeated table-row structure,
    where the real caption is attached to an earlier sibling)."""
    text = ""
    for window in (CONTEXT_CHARS, CONTEXT_CHARS * 2, CONTEXT_CHARS * 4, CONTEXT_CHARS * 6):
        start = max(0, position - window)
        fragment = full_html[start:position]
        text = clean_text(fragment)
        # prefer a window that captures at least one full sentence, not
        # just a fragment of adjacent markup (common in repeated-widget
        # table rows, e.g. chap3's softmax sliders)
        if len(text) >= 80 and ". " in text:
            break
    if not text:
        return "(no preceding prose found near this figure)"
    # trim to last ~260 chars, snapped to a sentence boundary if possible
    tail = text[-260:]
    dot = tail.find(". ")
    if 0 <= dot < 140:
        tail = tail[dot + 2 :]
    return tail.strip()


@dataclass
class Figure:
    page: str
    dom_id: str
    fig_type: str  # "d3-svg" | "canvas" | "other"
    position: int
    behavior: str


def find_figures(page: str, html_text: str) -> tuple[list[Figure], dict]:
    figures: list[Figure] = []

    seen_ids: set[str] = set()

    for m in DIV_ID_RE.finditer(html_text):
        dom_id = m.group(1)
        if DIV_ID_EXCLUDE_RE.match(dom_id):
            continue
        far_window = html_text[m.end() : m.end() + LOOKAHEAD_CHARS]
        near_window = html_text[m.end() : m.end() + NEAR_SCRIPT_CHARS]
        is_figure = False
        if D3_TOKEN_RE.search(far_window):
            # direct evidence: inline d3 API calls, or a <script src=".../d3...">
            is_figure = True
        elif NEAR_SCRIPT_RE.search(near_window):
            # indirect evidence: div is immediately bound to a <script> (often
            # an externally-sourced draw script, e.g. js/wide_gaussian.js)
            # with no literal "d3." substring nearby. All such div-bound
            # scripts observed in this book are d3 draws (the page loads
            # d3.v3.min.js globally); classify as d3-svg.
            is_figure = True

        if is_figure:
            key = ("div", dom_id, m.start())
            if key in seen_ids:
                continue
            seen_ids.add(key)
            figures.append(
                Figure(
                    page=page,
                    dom_id=dom_id,
                    fig_type="d3-svg",
                    position=m.start(),
                    behavior=quote_context(html_text, m.start()),
                )
            )

    for m in CANVAS_ID_RE.finditer(html_text):
        dom_id = m.group(1)
        key = ("canvas", dom_id, m.start())
        if key in seen_ids:
            continue
        seen_ids.add(key)
        figures.append(
            Figure(
                page=page,
                dom_id=dom_id,
                fig_type="canvas",
                position=m.start(),
                behavior=quote_context(html_text, m.start()),
            )
        )

    figures.sort(key=lambda f: f.position)

    stats = {
        "d3_token_count": len(D3_TOKEN_RE.findall(html_text)),
        "canvas_tag_count": len(CANVAS_TAG_RE.findall(html_text)),
        "d3_figures": sum(1 for f in figures if f.fig_type == "d3-svg"),
        "canvas_figures": sum(1 for f in figures if f.fig_type == "canvas"),
    }
    return figures, stats


def write_inventory(pages_html: dict[str, str]) -> int:
    all_figures: dict[str, list[Figure]] = {}
    all_stats: dict[str, dict] = {}
    total = 0

    for page in PAGES:
        html_text = pages_html.get(page, "")
        figures, stats = find_figures(page, html_text)
        all_figures[page] = figures
        all_stats[page] = stats
        total += len(figures)

    lines: list[str] = []
    lines.append("# Interactive (JS-rendered) Figure Inventory")
    lines.append("")
    lines.append(
        "Generated by `tools/scrape.py`. Do not hand-edit — re-run the "
        "script to regenerate. Every figure below is rendered by "
        "client-side JS (D3 SVG or `<canvas>`), NOT a static `<img>`, so it "
        "is invisible to a naive scrape and needs a Phase 2 static "
        "fallback (§4.7) and a Phase 4 reimplementation."
    )
    lines.append("")
    lines.append(
        "`behavior` text is quoted verbatim from the prose immediately "
        "preceding the figure in the source HTML (tags stripped) — not "
        "guessed."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| Page | d3-svg figures | canvas figures | `d3.` tokens | `<canvas>` tags |"
    )
    lines.append("|---|---:|---:|---:|---:|")
    for page in PAGES:
        s = all_stats[page]
        lines.append(
            f"| {page} | {s['d3_figures']} | {s['canvas_figures']} | "
            f"{s['d3_token_count']} | {s['canvas_tag_count']} |"
        )
    lines.append("")
    lines.append(f"**Total JS-rendered figures across all pages: {total}**")
    lines.append("")
    lines.append("## Details")
    lines.append("")

    for page in PAGES:
        figures = all_figures[page]
        lines.append(f"### {page}")
        lines.append("")
        if not figures:
            lines.append("No JS-rendered (non-`<img>`) figures detected.")
            lines.append("")
            continue
        for i, fig in enumerate(figures, start=1):
            lines.append(
                f"{i}. **`#{fig.dom_id}`** — type: `{fig.fig_type}`, "
                f"page: `{fig.page}`"
            )
            lines.append(f"   - Behavior (quoted context): \"{fig.behavior}\"")
            lines.append("")

    INVENTORY_PATH.write_text("\n".join(lines) + "\n")
    return total


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download pages/images even if already present on disk.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.4,
        help="Seconds to sleep between network requests (politeness).",
    )
    args = parser.parse_args()

    session = make_session()

    print("== Step 1/4: downloading pages ==")
    page_results = download_pages(session, args.force, args.delay)
    pages_downloaded = sum(1 for p in page_results if p.downloaded)
    pages_skipped = len(page_results) - pages_downloaded

    pages_html = {p.name: p.path.read_text(encoding="utf-8", errors="replace") for p in page_results}

    print("\n== Step 2/4: downloading images ==")
    registry, page_refs, images_downloaded, images_skipped = download_images(
        session, pages_html, args.force, args.delay
    )
    on_disk_count = len([p for p in IMAGES_DIR.iterdir() if p.name != ".gitkeep"])

    print("\n== Step 3/4: writing ASSET_MANIFEST.json ==")
    write_manifest(registry, page_refs)
    print(f"  wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")

    print("\n== Step 4/4: writing INTERACTIVE_INVENTORY.md ==")
    total_figures = write_inventory(pages_html)
    print(f"  wrote {INVENTORY_PATH.relative_to(REPO_ROOT)}")

    print("\n== Summary ==")
    print(f"  pages:  {len(page_results)} total, {pages_downloaded} downloaded, {pages_skipped} skipped (already present)")
    print(f"  images: {len(registry)} unique referenced, {images_downloaded} downloaded, {images_skipped} skipped (already present)")
    print(f"  on-disk images in docs/images/ = {on_disk_count}")
    print(f"  manifest total_images = {len(registry)}")
    print(f"  interactive figures found = {total_figures}")

    if len(registry) != on_disk_count:
        print(
            f"  [ERROR] manifest image count ({len(registry)}) != on-disk "
            f"file count ({on_disk_count})",
            file=sys.stderr,
        )
        return 1

    if pages_downloaded == 0 and images_downloaded == 0 and not args.force:
        print("  NO-OP: everything already present on disk; zero network requests for pages/images.")
    else:
        print(f"  NETWORK ACTIVITY: {pages_downloaded} page(s) + {images_downloaded} image(s) fetched over HTTP.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
