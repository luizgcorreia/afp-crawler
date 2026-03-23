import csv
from pathlib import Path

from merge_afp_topics_into_metadata import deduplicate_topics, merge_topic_columns, topic_depth, write_csv_rows


def test_topic_depth_counts_non_empty_topic_columns():
    assert topic_depth({"topic1": "Computer science", "topic2": "", "topic3": ""}) == 1
    assert topic_depth({"topic1": "Computer science", "topic2": "Algorithms", "topic3": ""}) == 2
    assert topic_depth({"topic1": "Computer science", "topic2": "Algorithms", "topic3": "Approximation"}) == 3


def test_deduplicate_topics_keeps_richer_and_later_rows():
    rows = [
        {"id": "Alpha", "topic1": "Computer science", "topic2": "", "topic3": ""},
        {"id": "Alpha", "topic1": "Computer science", "topic2": "Algorithms", "topic3": ""},
        {"id": "Alpha", "topic1": "Computer science", "topic2": "Algorithms", "topic3": "Approximation"},
        {"id": "Beta", "topic1": "Logic", "topic2": "", "topic3": ""},
        {"id": "Beta", "topic1": "Mathematics", "topic2": "", "topic3": ""},
    ]

    deduplicated = deduplicate_topics(rows)

    assert deduplicated["Alpha"] == {
        "id": "Alpha",
        "topic1": "Computer science",
        "topic2": "Algorithms",
        "topic3": "Approximation",
    }
    assert deduplicated["Beta"] == {
        "id": "Beta",
        "topic1": "Mathematics",
        "topic2": "",
        "topic3": "",
    }


def test_merge_topic_columns_adds_domain_clusters():
    metadata_rows = [
        {"id": "Alpha", "title": "Alpha entry"},
        {"id": "Gamma", "title": "Gamma entry"},
    ]
    topics_by_id = {
        "Alpha": {
            "id": "Alpha",
            "topic1": "Computer science",
            "topic2": "Algorithms",
            "topic3": "Approximation",
        }
    }

    merged = merge_topic_columns(metadata_rows, topics_by_id)

    assert merged == [
        {
            "id": "Alpha",
            "title": "Alpha entry",
            "domain_cluster1": "Computer science",
            "domain_cluster2": "Algorithms",
            "domain_cluster3": "Approximation",
        },
        {
            "id": "Gamma",
            "title": "Gamma entry",
            "domain_cluster1": "",
            "domain_cluster2": "",
            "domain_cluster3": "",
        },
    ]


def test_write_csv_rows_round_trips_output(tmp_path: Path):
    output_path = tmp_path / "merged.csv"
    rows = [
        {
            "id": "Alpha",
            "title": "Alpha entry",
            "domain_cluster1": "Computer science",
            "domain_cluster2": "Algorithms",
            "domain_cluster3": "Approximation",
        }
    ]

    write_csv_rows(output_path, rows, list(rows[0].keys()))

    with output_path.open(newline="", encoding="utf-8") as handle:
        loaded = list(csv.DictReader(handle))
    assert loaded == rows
