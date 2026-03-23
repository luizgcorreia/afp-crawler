import csv
from pathlib import Path

from afp_topics_to_csv import entry_id_from_url, topic_levels, write_csv


def test_entry_id_from_url_strips_html_extension():
    assert (
        entry_id_from_url("https://www.isa-afp.org/entries/Dynamic_Pushdown_Networks.html")
        == "Dynamic_Pushdown_Networks"
    )


def test_topic_levels_pads_missing_levels():
    assert topic_levels("Computer science") == ("Computer science", "", "")
    assert topic_levels("Computer science/Algorithms") == ("Computer science", "Algorithms", "")
    assert topic_levels("Computer science/Algorithms/Approximation") == (
        "Computer science",
        "Algorithms",
        "Approximation",
    )


def test_write_csv_emits_one_row_per_topic_entry_assignment(tmp_path: Path):
    dataset = {
        "topics": [
            {
                "page_title": "Computer science",
                "entries": ["https://www.isa-afp.org/entries/Dynamic_Pushdown_Networks.html"],
            },
            {
                "page_title": "Computer science/Algorithms/Approximation",
                "entries": [
                    "https://www.isa-afp.org/entries/Concentrated_Liquidity_Market_Making_Operations.html",
                    "https://www.isa-afp.org/entries/Set_Reconciliation.html",
                ],
            },
        ]
    }
    output_path = tmp_path / "afp_topics.csv"

    row_count = write_csv(dataset, output_path)

    assert row_count == 3
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "id": "Dynamic_Pushdown_Networks",
            "topic1": "Computer science",
            "topic2": "",
            "topic3": "",
        },
        {
            "id": "Concentrated_Liquidity_Market_Making_Operations",
            "topic1": "Computer science",
            "topic2": "Algorithms",
            "topic3": "Approximation",
        },
        {
            "id": "Set_Reconciliation",
            "topic1": "Computer science",
            "topic2": "Algorithms",
            "topic3": "Approximation",
        },
    ]
