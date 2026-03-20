# AFP topics crawler

This repository contains a small Python crawler for the Archive of Formal Proofs topics index at <https://www.isa-afp.org/topics/>. It visits every topic page listed on the index, including top-level topics that can have their own theory assignments, and collects the AFP entry URLs found on each page.

## Included dataset

The repository also checks in a generated dataset at `afp_topics.json`. Regenerate it with:

```bash
python3 afp_topics_crawler.py --output afp_topics.json
```

## Usage

```bash
python3 afp_topics_crawler.py --output afp_topics.json
```

The generated JSON contains:

- the topics index URL,
- the UTC crawl timestamp,
- the number of topic pages discovered,
- the total number of topic-to-entry links collected,
- one record per topic with:
  - topic name,
  - topic page title,
  - topic page URL,
  - expected count from the topics index,
  - extracted entry count,
  - a boolean indicating whether the extracted count matches the index,
  - the list of AFP entry URLs.

## Notes

- The crawler uses only the Python standard library.
- Entry URLs are normalized to absolute `https://www.isa-afp.org/entries/...html` links.
- Duplicate entry links on a topic page are removed while preserving page order.
