#!/usr/bin/env python3
"""Consistency audit for the generated LINKO manuscript.

Checks that
1. every numeric value printed in the manuscript body is present in the
   generated result files (no value is typed by hand);
2. citations are numbered in order of first appearance with no orphans;
3. every table and figure is cited in the text before it appears;
4. banned overclaiming phrases are absent;
5. the abstract respects the Statistics in Medicine word limit.

Exit code 1 on any failure.
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE.parent))

from icr_paper.src.manuscript_content import (
    build_english,
    renumber_citations,
)
from icr_paper.src.results_loader import load_results

RESULTS_DIR = BASE / "results"
NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")
CITATION_RE = re.compile(r"\[(\d+(?:,\d+)*)\]")
BANNED = [
    "validity of pooling",
    "robust validation",
    "conclusively",
    "proves",
    "confirms the validity",
    "significantly faster",
]
# Values that describe the data-generating mechanism, the estimators or the
# journal format rather than a computed result.
ALLOWED_LITERALS = {
    "0.3", "0.5", "0.25", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "0", "20", "25", "40", "80", "200", "95", "14", "250", "1.0", "0.0",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10",
    "3.1", "3.2", "3.3", "3.4", "3.5", "1000", "500", "100",
}


def result_number_pool() -> set:
    """All numbers appearing anywhere in the generated result files."""
    pool = set()

    def add(value):
        if isinstance(value, bool) or value is None:
            return
        if isinstance(value, (int, float)):
            for digits in range(7):
                pool.add(f"{value:.{digits}f}".rstrip("0").rstrip("."))
                pool.add(f"{value:.{digits}f}")
                pool.add(f"{value:,.{digits}f}")
            pool.add(str(value))
        elif isinstance(value, dict):
            for item in value.values():
                add(item)
        elif isinstance(value, list):
            for item in value:
                add(item)

    raw_json = (RESULTS_DIR / "results.json").read_text()
    add(json.loads(raw_json))
    # Identifiers and version strings quoted in the manuscript (git commit,
    # software versions) appear verbatim in the metadata.
    pool.update(NUMBER_RE.findall(raw_json))
    for path in RESULTS_DIR.glob("*.csv"):
        for token in NUMBER_RE.findall(path.read_text()):
            add(float(token.replace(",", "")))
            pool.add(token)
    # Percentages and derived displays.
    for value in list(pool):
        try:
            number = float(value.replace(",", ""))
        except ValueError:
            continue
        for digits in range(4):
            pool.add(f"{number * 100:.{digits}f}")
            pool.add(f"{number * 100:.{digits}f}".rstrip("0").rstrip("."))
            pool.add(f"{abs(number):.{digits}f}")
    return pool


def audit() -> list:
    problems = []
    results = load_results()
    blocks = renumber_citations(build_english(results))
    pool = result_number_pool()

    body = []
    tables, figures = [], []
    reference_count = 0
    for kind, payload in blocks:
        if kind in ("p", "eq", "title", "h1", "h2", "h3"):
            body.append((kind, payload))
        elif kind == "table":
            tables.append(payload["label"])
            body.append(("caption", payload["caption"]))
        elif kind == "figure":
            figures.append(payload["label"])
            body.append(("caption", payload["caption"]))
        elif kind == "references":
            reference_count = len(payload)

    text = "\n".join(t for _, t in body)

    # 1. numbers traceable to generated results
    for kind, payload in body:
        if kind not in ("p", "caption"):
            continue
        # Identifiers (URLs, DOIs, handles, commit hashes) are not results.
        stripped = re.sub(r"\S*(?:https?://|doi|/|:)\S*", " ", payload)
        stripped = CITATION_RE.sub("", stripped)
        for token in NUMBER_RE.findall(stripped):
            clean = token.lstrip("-")
            if clean in ALLOWED_LITERALS or clean in pool:
                continue
            if clean.replace(",", "") in pool:
                continue
            problems.append(
                f"Untraceable number '{token}' in: {payload[:90]}..."
            )

    # 2. citation order and orphans
    seen = 0
    for match in CITATION_RE.finditer(text):
        for number in (int(n) for n in match.group(1).split(",")):
            if number > reference_count:
                problems.append(f"Citation {number} exceeds reference count")
            if number > seen + 1:
                problems.append(f"Citation {number} appears before {seen + 1}")
            seen = max(seen, number)
    if seen != reference_count:
        problems.append(
            f"{reference_count} references but highest citation is {seen}"
        )

    # 3. figures and tables cited in order
    for labels in (tables, figures):
        position = -1
        for label in labels:
            mention = text.find(label)
            if mention < 0:
                problems.append(f"{label} is never cited in the text")
            elif mention < position:
                problems.append(f"{label} is cited out of order")
            else:
                position = mention

    # 4. overclaiming
    lowered = text.lower()
    for phrase in BANNED:
        if phrase in lowered:
            problems.append(f"Overclaiming phrase present: '{phrase}'")

    # 5. abstract length
    for index, (kind, payload) in enumerate(blocks):
        if kind == "h1" and payload == "Abstract":
            words = len(CITATION_RE.sub("", blocks[index + 1][1]).split())
            if words > 250:
                problems.append(f"Abstract is {words} words (limit 250)")
    return problems


def main() -> None:
    problems = audit()
    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print("Manuscript audit passed.")


if __name__ == "__main__":
    main()
