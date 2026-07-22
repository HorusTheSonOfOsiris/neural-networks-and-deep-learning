#!/usr/bin/env python3
"""Verify Plan.md section 7 checks 1-6 for every generated chapter.

The raw HTML snapshots are the input of record.  This script compares them
with docs/chap1.md through docs/chap6.md and fails loudly when generated book
content has drifted or an extractor regression has reappeared.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Tag
import markdown


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "raw"
DOCS_DIR = REPO_ROOT / "docs"
INVENTORY_PATH = RAW_DIR / "INTERACTIVE_INVENTORY.md"
CHAPTERS = tuple(f"chap{number}" for number in range(1, 7))

EQNARRAY_RE = re.compile(
    r"\\begin\{eqnarray\}.*?\\end\{eqnarray\}", re.DOTALL
)
TAG_RE = re.compile(r"\\tag\{([^}]+)\}")
PYTHON_FENCE_RE = re.compile(
    r"^```python[ \t]*\n(.*?)^```[ \t]*$", re.DOTALL | re.MULTILINE
)
CONTROL_WHITESPACE_RE = re.compile(r"[\t\r\n]")


@dataclass(frozen=True)
class Failure:
    page: str
    check: int
    message: str


@dataclass(frozen=True)
class ChapterStats:
    equations: int
    headings: int
    sidenotes: int
    images: int
    code_blocks: int
    interactives: int


def normalize_anchor_id(value: str) -> str:
    """Match browser normalization used by the converter for source IDs."""
    return CONTROL_WHITESPACE_RE.sub("", value).strip()


def normalize_code(value: str) -> str:
    """Plan section 7 uses a trailing-whitespace-normalized code diff."""
    return "\n".join(line.rstrip() for line in value.strip("\n").splitlines())


def render_markdown(markdown_text: str) -> BeautifulSoup:
    html = markdown.markdown(
        markdown_text,
        extensions=[
            "attr_list",
            "admonition",
            "footnotes",
            "toc",
            "pymdownx.superfences",
            "pymdownx.arithmatex",
        ],
        extension_configs={"pymdownx.arithmatex": {"generic": True}},
    )
    return BeautifulSoup(html, "html.parser")


def inventory_ids(inventory_text: str, page_name: str) -> set[str]:
    section = re.search(
        rf"^### {re.escape(page_name)}\s*$", inventory_text, re.MULTILINE
    )
    if section is None:
        return set()
    remainder = inventory_text[section.end() :]
    next_section = re.search(r"^### ", remainder, re.MULTILINE)
    body = remainder[: next_section.start()] if next_section else remainder
    return set(re.findall(r"\*\*`#([\w-]+)`\*\*", body))


def element_ids(soup: BeautifulSoup) -> Counter[str]:
    return Counter(
        normalize_anchor_id(str(tag["id"]))
        for tag in soup.find_all(attrs={"id": True})
    )


def source_section(source_html: str) -> Tag | None:
    soup = BeautifulSoup(source_html, "lxml")
    section = soup.find("div", class_="section")
    if section is None:
        return None
    toc = section.find(id="toc")
    if toc is not None:
        toc.decompose()
    return section


def content_image_sources(section: Tag) -> Counter[str]:
    """Exclude TOC/UI chrome; book content images live below images/."""
    return Counter(
        src
        for image in section.find_all("img")
        if (src := image.get("src", "")).startswith("images/")
        and Path(urlsplit(src).path).name != "arrow.png"
    )


def output_image_sources(soup: BeautifulSoup) -> Counter[str]:
    return Counter(
        src
        for image in soup.find_all("img")
        if (src := image.get("src", "")).startswith("images/")
        and Path(urlsplit(src).path).name != "arrow.png"
    )


def verify_chapter_content(
    page: str,
    source_html: str,
    output_markdown: str,
    expected_interactives: set[str],
) -> tuple[list[Failure], ChapterStats]:
    failures: list[Failure] = []
    section = source_section(source_html)
    rendered = render_markdown(output_markdown)

    if section is None:
        failures.append(Failure(page, 1, "raw source has no div.section"))
        return failures, ChapterStats(0, 0, 0, 0, 0, 0)

    output_ids = element_ids(rendered)

    # Check 1: every real eqnarray is represented by one math-display block,
    # and no bare environment survives outside that wrapper.
    source_math = [
        block for block in EQNARRAY_RE.findall(source_html) if TAG_RE.search(block)
    ]
    math_displays = rendered.select("div.math-display")
    if len(math_displays) != len(source_math):
        failures.append(
            Failure(
                page,
                1,
                f"math-display count {len(math_displays)} != "
                f"source eqnarray count {len(source_math)}",
            )
        )
    leaked_math = [
        node
        for node in rendered.find_all(string=re.compile(r"\\begin\{eqnarray\}"))
        if node.find_parent("div", class_="math-display") is None
    ]
    if leaked_math:
        failures.append(
            Failure(page, 1, f"{len(leaked_math)} raw eqnarray block(s) outside math-display")
        )

    # Check 2: tags and equation anchors are one-for-one, including BP tags
    # and additional anchors in shared multi-tag environments.
    source_tags = Counter(TAG_RE.findall(source_html))
    output_tags = Counter(
        TAG_RE.findall("\n".join(display.get_text() for display in math_displays))
    )
    if output_tags != source_tags:
        missing = source_tags - output_tags
        extra = output_tags - source_tags
        failures.append(
            Failure(page, 2, f"equation tag mismatch; missing={dict(missing)}, extra={dict(extra)}")
        )

    source_equation_ids = Counter(
        normalize_anchor_id(str(anchor.get("name", "")))
        for anchor in section.select("a.displaced_anchor[name]")
    )
    output_equation_ids = Counter(
        anchor_id for anchor_id, count in output_ids.items() for _ in range(count)
        if anchor_id.startswith("eqtn")
    )
    if output_equation_ids != source_equation_ids:
        missing = source_equation_ids - output_equation_ids
        extra = output_equation_ids - source_equation_ids
        failures.append(
            Failure(
                page,
                2,
                f"equation anchor mismatch; missing={dict(missing)}, extra={dict(extra)}",
            )
        )
    for label in source_tags:
        anchor_id = f"eqtn{label}"
        if output_ids[anchor_id] != 1:
            failures.append(
                Failure(
                    page,
                    2,
                    f"#{anchor_id} occurs {output_ids[anchor_id]} times; expected once",
                )
            )

    # Check 3: every named source heading retains its exact normalized ID.
    source_heading_ids = [
        normalize_anchor_id(str(anchor["name"]))
        for heading in section.find_all(["h3", "h4"])
        if (anchor := heading.find("a", attrs={"name": True})) is not None
    ]
    for heading_id in source_heading_ids:
        if output_ids[heading_id] != 1:
            failures.append(
                Failure(
                    page,
                    3,
                    f"heading #{heading_id} occurs {output_ids[heading_id]} times; expected once",
                )
            )

    # The remaining structural leakage checks protect against the source's
    # hidden equation copies, scripts/styles, and merged margin notes.
    for token in ("marginequation", "<script", "<style"):
        if token.lower() in output_markdown.lower():
            failures.append(Failure(page, 2, f"forbidden source artifact leaked: {token}"))

    source_sidenotes = len(section.select("span.marginnote"))
    output_sidenotes = len(rendered.select("span.sidenote"))
    if output_sidenotes != source_sidenotes:
        failures.append(
            Failure(
                page,
                3,
                f"sidenote count {output_sidenotes} != source marginnote count {source_sidenotes}",
            )
        )

    # Check 5: compare image identities/counts, then require one captioned
    # placeholder for every inventoried JS figure.
    source_images = content_image_sources(section)
    output_images = output_image_sources(rendered)
    if output_images != source_images:
        missing = source_images - output_images
        extra = output_images - source_images
        failures.append(
            Failure(page, 5, f"image mismatch; missing={dict(missing)}, extra={dict(extra)}")
        )

    placeholder_ids = Counter(
        normalize_anchor_id(str(placeholder.get("id", "")))
        for placeholder in rendered.select("div.interactive-placeholder")
    )
    expected_placeholder_ids = Counter(expected_interactives)
    if placeholder_ids != expected_placeholder_ids:
        missing = expected_placeholder_ids - placeholder_ids
        extra = placeholder_ids - expected_placeholder_ids
        failures.append(
            Failure(
                page,
                5,
                f"interactive placeholder mismatch; missing={dict(missing)}, extra={dict(extra)}",
            )
        )
    for placeholder in rendered.select("div.interactive-placeholder"):
        if placeholder.find("a", href=True) is None:
            failures.append(
                Failure(
                    page,
                    5,
                    f"interactive #{placeholder.get('id', '')} has no original-site link",
                )
            )

    # Check 6: source and generated Python 2.7 blocks must remain identical
    # after the whitespace normalization required by Plan.md.
    source_code = [pre.get_text() for pre in section.select("div.highlight pre")]
    output_code = PYTHON_FENCE_RE.findall(output_markdown)
    if len(output_code) != len(source_code):
        failures.append(
            Failure(
                page,
                6,
                f"code block count {len(output_code)} != source count {len(source_code)}",
            )
        )
    for index, (source_block, output_block) in enumerate(
        zip(source_code, output_code), start=1
    ):
        if normalize_code(output_block) != normalize_code(source_block):
            failures.append(Failure(page, 6, f"code block {index} differs from source"))

    stats = ChapterStats(
        equations=sum(source_tags.values()),
        headings=len(source_heading_ids),
        sidenotes=source_sidenotes,
        images=sum(source_images.values()),
        code_blocks=len(source_code),
        interactives=len(expected_interactives),
    )
    return failures, stats


def load_rendered_docs(docs_dir: Path) -> dict[Path, BeautifulSoup]:
    return {
        path.resolve(): render_markdown(path.read_text(encoding="utf-8"))
        for path in docs_dir.glob("*.md")
    }


def verify_local_links(docs_dir: Path) -> list[Failure]:
    """Check local targets and fragments; MkDocs strict misses some anchors."""
    failures: list[Failure] = []
    rendered_docs = load_rendered_docs(docs_dir)
    docs_root = docs_dir.resolve()

    for current_path, soup in rendered_docs.items():
        page = current_path.name
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            parsed = urlsplit(href)
            if not href or parsed.scheme or parsed.netloc or href.startswith("//"):
                continue

            relative_path = unquote(parsed.path)
            target = (
                current_path
                if not relative_path
                else (current_path.parent / relative_path).resolve()
            )
            try:
                target.relative_to(docs_root)
            except ValueError:
                failures.append(Failure(page, 4, f"local link escapes docs/: {href}"))
                continue

            if not target.exists():
                failures.append(Failure(page, 4, f"local link target does not exist: {href}"))
                continue

            fragment = unquote(parsed.fragment)
            if not fragment:
                continue
            target_soup = rendered_docs.get(target)
            if target_soup is None:
                failures.append(Failure(page, 4, f"fragment targets a non-page file: {href}"))
                continue
            if target_soup.find(id=fragment) is None:
                failures.append(Failure(page, 4, f"anchor target does not exist: {href}"))

    return failures


def verify_image_files(docs_dir: Path) -> list[Failure]:
    failures: list[Failure] = []
    for chapter in CHAPTERS:
        markdown_path = docs_dir / f"{chapter}.md"
        if not markdown_path.exists():
            continue
        soup = render_markdown(markdown_path.read_text(encoding="utf-8"))
        for image in soup.find_all("img", src=True):
            src = str(image["src"])
            parsed = urlsplit(src)
            if parsed.scheme or parsed.netloc:
                continue
            target = (markdown_path.parent / unquote(parsed.path)).resolve()
            if not target.is_file():
                failures.append(Failure(f"{chapter}.html", 5, f"image file is missing: {src}"))
    return failures


def run_strict_build(repo_root: Path) -> Failure | None:
    with tempfile.TemporaryDirectory(prefix="nndl-verify-") as site_dir:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mkdocs",
                "build",
                "--strict",
                "--site-dir",
                site_dir,
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    if result.returncode == 0:
        return None
    details = (result.stderr or result.stdout).strip().splitlines()
    summary = details[-1] if details else f"exit status {result.returncode}"
    return Failure("repository", 4, f"mkdocs build --strict failed: {summary}")


def verify_repository(
    repo_root: Path = REPO_ROOT, *, run_build: bool = True
) -> tuple[list[Failure], dict[str, ChapterStats]]:
    raw_dir = repo_root / "raw"
    docs_dir = repo_root / "docs"
    inventory_path = raw_dir / "INTERACTIVE_INVENTORY.md"
    failures: list[Failure] = []
    stats: dict[str, ChapterStats] = {}

    if not inventory_path.exists():
        return [Failure("repository", 5, "interactive inventory is missing")], stats
    inventory_text = inventory_path.read_text(encoding="utf-8")

    for chapter in CHAPTERS:
        page_name = f"{chapter}.html"
        source_path = raw_dir / page_name
        output_path = docs_dir / f"{chapter}.md"
        if not source_path.exists():
            failures.append(Failure(page_name, 1, f"missing source: {source_path}"))
            continue
        if not output_path.exists():
            failures.append(Failure(page_name, 1, f"missing output: {output_path}"))
            continue
        chapter_failures, chapter_stats = verify_chapter_content(
            page_name,
            source_path.read_text(encoding="utf-8"),
            output_path.read_text(encoding="utf-8"),
            inventory_ids(inventory_text, page_name),
        )
        failures.extend(chapter_failures)
        stats[chapter] = chapter_stats

    failures.extend(verify_local_links(docs_dir))
    failures.extend(verify_image_files(docs_dir))
    if run_build:
        build_failure = run_strict_build(repo_root)
        if build_failure is not None:
            failures.append(build_failure)
    return failures, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="skip the temporary mkdocs --strict check (for focused development only)",
    )
    args = parser.parse_args(argv)

    failures, stats = verify_repository(run_build=not args.skip_build)
    failed_pages = {failure.page for failure in failures}
    for chapter in CHAPTERS:
        page = f"{chapter}.html"
        chapter_stats = stats.get(chapter)
        if chapter_stats is not None and page not in failed_pages:
            print(
                f"PASS {page}: {chapter_stats.equations} tags, "
                f"{chapter_stats.headings} headings, {chapter_stats.sidenotes} sidenotes, "
                f"{chapter_stats.images} images, {chapter_stats.code_blocks} code blocks, "
                f"{chapter_stats.interactives} interactives"
            )

    if failures:
        for failure in failures:
            print(
                f"FAIL {failure.page} [check {failure.check}]: {failure.message}",
                file=sys.stderr,
            )
        print(f"Verification failed with {len(failures)} error(s).", file=sys.stderr)
        return 1

    print("PASS repository: Plan.md section 7 checks 1-6 are clean for all chapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
