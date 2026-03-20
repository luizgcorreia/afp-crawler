# AFP topics crawler

This repository contains small Python tools for the Archive of Formal Proofs topics index at <https://www.isa-afp.org/topics/>.

- `afp_topics_crawler.py` crawls the live topics pages and builds a JSON dataset.
- `afp_topics_to_csv.py` converts that JSON dataset into a CSV with one row per topic-entry assignment.

## Included datasets

The repository checks in two generated datasets:

- `afp_topics.json`: the crawled topics dataset with per-topic entry URLs.
- `afp_topics.csv`: a flattened CSV with columns `id,topic1,topic2,topic3`.

Regenerate them with:

```bash
python3 afp_topics_crawler.py --output afp_topics.json
python3 afp_topics_to_csv.py --input afp_topics.json --output afp_topics.csv
```

## CSV format

`afp_topics.csv` contains one row per topic-entry assignment from `afp_topics.json`.

- `id`: the AFP entry filename without the `.html` extension.
- `topic1`, `topic2`, `topic3`: the topic hierarchy extracted from the AFP page title.

For example, the entry URL `https://www.isa-afp.org/entries/Dynamic_Pushdown_Networks.html` becomes the CSV id `Dynamic_Pushdown_Networks`.

## JSON format

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

- The tools use only the Python standard library.
- Entry URLs are normalized to absolute `https://www.isa-afp.org/entries/...html` links.
- Duplicate entry links on a topic page are removed while preserving page order.
- The CSV keeps the AFP topic labels exactly as they appear in the topic page titles.
