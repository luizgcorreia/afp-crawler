#!/usr/bin/env python3
"""Crawl AFP topic pages and collect theory entry links."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from urllib.error import URLError
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

BASE_URL = "https://www.isa-afp.org"
TOPICS_INDEX_URL = f"{BASE_URL}/topics/"
DEFAULT_USER_AGENT = "afp-topics-crawler/0.1 (+https://www.isa-afp.org/topics/)"
COUNT_SUFFIX_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<count>\d+)\)\s*$")


@dataclass(frozen=True)
class TopicRef:
    name: str
    topic_url: str
    expected_count: int | None = None


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.heading_texts: dict[str, list[str]] = {"h1": []}
        self._current_href: str | None = None
        self._current_link_chunks: list[str] = []
        self._active_heading: str | None = None
        self._heading_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a":
            self._current_href = attrs_dict.get("href")
            self._current_link_chunks = []
        if tag in self.heading_texts:
            self._active_heading = tag
            self._heading_chunks = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_link_chunks.append(data)
        if self._active_heading is not None:
            self._heading_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            text = normalize_whitespace("".join(self._current_link_chunks))
            self.links.append((self._current_href, text))
            self._current_href = None
            self._current_link_chunks = []
        if tag == self._active_heading and self._active_heading is not None:
            text = normalize_whitespace("".join(self._heading_chunks))
            if text:
                self.heading_texts[self._active_heading].append(text)
            self._active_heading = None
            self._heading_chunks = []


class TopicPageParser(LinkCollector):
    @property
    def title(self) -> str | None:
        titles = self.heading_texts.get("h1") or []
        return titles[0] if titles else None


class TopicsIndexParser(LinkCollector):
    def topic_refs(self, base_url: str = BASE_URL) -> list[TopicRef]:
        seen: set[str] = set()
        topics: list[TopicRef] = []
        for href, text in self.links:
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            if not parsed.path.startswith("/topics/") or parsed.path == "/topics/":
                continue
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            name, expected_count = parse_topic_label(text)
            topics.append(TopicRef(name=name, topic_url=absolute_url, expected_count=expected_count))
        return topics


@dataclass(frozen=True)
class TopicEntries:
    name: str
    topic_url: str
    page_title: str | None
    expected_count: int | None
    entries: list[str]


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def parse_topic_label(text: str) -> tuple[str, int | None]:
    text = normalize_whitespace(text)
    match = COUNT_SUFFIX_RE.match(text)
    if not match:
        return text, None
    return match.group("name"), int(match.group("count"))


class CrawlError(RuntimeError):
    """Raised when a page cannot be fetched."""


def fetch_html(url: str, *, user_agent: str = DEFAULT_USER_AGENT, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except URLError as exc:
        raise CrawlError(f"failed to fetch {url}: {exc}") from exc


def parse_topics_index(html: str, *, base_url: str = BASE_URL) -> list[TopicRef]:
    parser = TopicsIndexParser()
    parser.feed(html)
    return parser.topic_refs(base_url)


def parse_topic_entries(html: str, topic: TopicRef, *, base_url: str = BASE_URL) -> TopicEntries:
    parser = TopicPageParser()
    parser.feed(html)

    entries: list[str] = []
    seen_entries: set[str] = set()
    for href, _text in parser.links:
        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)
        if not parsed.path.startswith("/entries/") or not parsed.path.endswith(".html"):
            continue
        if absolute_url in seen_entries:
            continue
        seen_entries.add(absolute_url)
        entries.append(absolute_url)

    return TopicEntries(
        name=topic.name,
        topic_url=topic.topic_url,
        page_title=parser.title,
        expected_count=topic.expected_count,
        entries=entries,
    )


def crawl_topics(index_url: str = TOPICS_INDEX_URL) -> list[TopicEntries]:
    index_html = fetch_html(index_url)
    topics = parse_topics_index(index_html, base_url=index_url)
    return [parse_topic_entries(fetch_html(topic.topic_url), topic, base_url=index_url) for topic in topics]


def build_output(
    topics: Iterable[TopicEntries],
    *,
    topics_index_url: str = TOPICS_INDEX_URL,
    crawled_at_utc: str | None = None,
) -> dict[str, object]:
    topic_list = list(topics)
    total_entry_links = sum(len(topic.entries) for topic in topic_list)
    if crawled_at_utc is None:
        crawled_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "topics_index_url": topics_index_url,
        "crawled_at_utc": crawled_at_utc,
        "topic_count": len(topic_list),
        "total_topic_entry_links": total_entry_links,
        "topics": [
            {
                "name": topic.name,
                "page_title": topic.page_title,
                "topic_url": topic.topic_url,
                "expected_count": topic.expected_count,
                "entry_count": len(topic.entries),
                "count_matches_index": topic.expected_count is None or topic.expected_count == len(topic.entries),
                "entries": topic.entries,
            }
            for topic in topic_list
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-url", default=TOPICS_INDEX_URL, help="AFP topics index URL to crawl")
    parser.add_argument("--output", type=Path, help="Optional JSON file to write")
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level for stdout/file output (default: 2)",
    )
    args = parser.parse_args(argv)

    try:
        topics = crawl_topics(args.index_url)
    except CrawlError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    payload = build_output(topics, topics_index_url=args.index_url)
    serialized = json.dumps(payload, indent=args.indent, sort_keys=False)

    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        sys.stdout.write(serialized + "\n")

    mismatches = [topic for topic in topics if topic.expected_count is not None and topic.expected_count != len(topic.entries)]
    if mismatches:
        print(
            f"warning: {len(mismatches)} topics had entry counts that differed from the topics index",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
