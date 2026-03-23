#!/usr/bin/env python3
"""Convert the AFP topics JSON dataset into a CSV with topic hierarchy columns."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlparse

MAX_TOPIC_LEVELS = 3


def entry_id_from_url(entry_url: str) -> str:
    path = Path(urlparse(entry_url).path)
    if path.suffix != ".html":
        raise ValueError(f"expected an .html entry URL, got: {entry_url}")
    return path.stem


def topic_levels(page_title: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in page_title.split("/") if part.strip()]
    if not 1 <= len(parts) <= MAX_TOPIC_LEVELS:
        raise ValueError(f"expected between 1 and {MAX_TOPIC_LEVELS} topic levels, got {page_title!r}")
    padded = parts + [""] * (MAX_TOPIC_LEVELS - len(parts))
    return padded[0], padded[1], padded[2]


def iter_csv_rows(dataset: dict[str, object]):
    for topic in dataset["topics"]:
        level1, level2, level3 = topic_levels(topic["page_title"])
        for entry_url in topic["entries"]:
            yield {
                "id": entry_id_from_url(entry_url),
                "topic1": level1,
                "topic2": level2,
                "topic3": level3,
            }


def write_csv(dataset: dict[str, object], output_path: Path) -> int:
    rows = list(iter_csv_rows(dataset))
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "topic1", "topic2", "topic3"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("afp_topics.json"), help="Input AFP topics JSON file")
    parser.add_argument("--output", type=Path, default=Path("afp_topics.csv"), help="Output CSV file")
    args = parser.parse_args(argv)

    dataset = json.loads(args.input.read_text(encoding="utf-8"))
    row_count = write_csv(dataset, args.output)
    print(f"wrote {row_count} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
