#!/usr/bin/env python3
"""Merge AFP topic clusters into a metadata CSV on the id column."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

TOPIC_COLUMNS = ("topic1", "topic2", "topic3")
DOMAIN_COLUMNS = ("domain_cluster1", "domain_cluster2", "domain_cluster3")


def configure_csv_field_size_limit() -> int:
    limit = sys.maxsize
    while True:
        try:
            return csv.field_size_limit(limit)
        except OverflowError:
            limit //= 10


def topic_depth(row: dict[str, str]) -> int:
    return sum(1 for column in TOPIC_COLUMNS if row.get(column, "").strip())


def deduplicate_topics(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    best_by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        entry_id = row["id"]
        current_best = best_by_id.get(entry_id)
        if current_best is None or topic_depth(row) >= topic_depth(current_best):
            best_by_id[entry_id] = row
    return best_by_id


def merge_topic_columns(
    metadata_rows: list[dict[str, str]],
    topic_rows_by_id: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    merged_rows: list[dict[str, str]] = []
    for row in metadata_rows:
        merged_row = dict(row)
        topic_row = topic_rows_by_id.get(row["id"], {})
        for topic_column, domain_column in zip(TOPIC_COLUMNS, DOMAIN_COLUMNS):
            merged_row[domain_column] = topic_row.get(topic_column, "")
        merged_rows.append(merged_row)
    return merged_rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    configure_csv_field_size_limit()
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def output_fieldnames(metadata_fieldnames: list[str]) -> list[str]:
    return metadata_fieldnames + [column for column in DOMAIN_COLUMNS if column not in metadata_fieldnames]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-csv", type=Path, required=True, help="Input metadata CSV with an id column")
    parser.add_argument("--topics-csv", type=Path, default=Path("afp_topics.csv"), help="AFP topics CSV file")
    parser.add_argument("--output", type=Path, required=True, help="Output merged CSV file")
    args = parser.parse_args(argv)

    metadata_rows = read_csv_rows(args.metadata_csv)
    topic_rows = read_csv_rows(args.topics_csv)

    metadata_fieldnames = list(metadata_rows[0].keys()) if metadata_rows else ["id"]
    merged_rows = merge_topic_columns(metadata_rows, deduplicate_topics(topic_rows))
    write_csv_rows(args.output, merged_rows, output_fieldnames(metadata_fieldnames))
    print(f"wrote {len(merged_rows)} merged rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
