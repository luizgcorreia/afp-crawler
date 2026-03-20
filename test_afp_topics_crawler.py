from afp_topics_crawler import TopicRef, build_output, parse_topic_entries, parse_topics_index


TOPICS_INDEX_HTML = """
<html><body>
<h2><a href="/topics/computer-science/">Computer science (6)</a></h2>
<ul>
  <li><a href="/topics/computer-science/algorithms/">Algorithms (54)</a></li>
  <li><a href="/topics/logic/">Logic (2)</a></li>
  <li><a href="/help/">Help</a></li>
</ul>
</body></html>
"""

TOPIC_PAGE_HTML = """
<html><body>
<h1>Computer science/Algorithms</h1>
<h5><a href="/entries/Concentrated_Liquidity_Market_Making_Operations.html">Concentrated Liquidity Market Making Operations</a></h5>
<p>by <a href="/authors/someone/">Someone</a></p>
<h5><a href="https://www.isa-afp.org/entries/Set_Reconciliation.html">Set Reconciliation</a></h5>
<h5><a href="/entries/Set_Reconciliation.html">Set Reconciliation</a></h5>
</body></html>
"""


def test_parse_topics_index_collects_all_topic_links_once():
    topics = parse_topics_index(TOPICS_INDEX_HTML)

    assert [(topic.name, topic.expected_count, topic.topic_url) for topic in topics] == [
        ("Computer science", 6, "https://www.isa-afp.org/topics/computer-science/"),
        ("Algorithms", 54, "https://www.isa-afp.org/topics/computer-science/algorithms/"),
        ("Logic", 2, "https://www.isa-afp.org/topics/logic/"),
    ]


def test_parse_topic_entries_filters_and_deduplicates_entry_links():
    topic = TopicRef("Algorithms", "https://www.isa-afp.org/topics/computer-science/algorithms/", 54)

    parsed = parse_topic_entries(TOPIC_PAGE_HTML, topic)

    assert parsed.page_title == "Computer science/Algorithms"
    assert parsed.entries == [
        "https://www.isa-afp.org/entries/Concentrated_Liquidity_Market_Making_Operations.html",
        "https://www.isa-afp.org/entries/Set_Reconciliation.html",
    ]


def test_build_output_includes_count_match_flag():
    topic = TopicRef("Algorithms", "https://www.isa-afp.org/topics/computer-science/algorithms/", 2)
    parsed = parse_topic_entries(TOPIC_PAGE_HTML, topic)

    payload = build_output(
        [parsed],
        topics_index_url="https://example.test/topics/",
        crawled_at_utc="2026-03-20T00:00:00+00:00",
    )

    assert payload["topics_index_url"] == "https://example.test/topics/"
    assert payload["crawled_at_utc"] == "2026-03-20T00:00:00+00:00"
    assert payload["topic_count"] == 1
    assert payload["total_topic_entry_links"] == 2
    assert payload["topics"][0]["count_matches_index"] is True
