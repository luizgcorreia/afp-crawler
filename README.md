# AFP topics crawler

This repository contains small Python tools for the Archive of Formal Proofs topics index at <https://www.isa-afp.org/topics/>.

- `afp_topics_crawler.py` crawls the live topics pages and builds a JSON dataset.
- `afp_topics_to_csv.py` converts that JSON dataset into a CSV with one row per topic-entry assignment.
- `merge_afp_topics_into_metadata.py` merges deduplicated topic clusters into another metadata CSV on the `id` column.

## Included datasets

The repository checks in two generated datasets:

- `afp_topics.json`: the crawled topics dataset with per-topic entry URLs and published years.
- `afp_topics.csv`: a flattened CSV with columns `id,topic1,topic2,topic3,published_year`.

Regenerate them with:

```bash
python3 afp_topics_crawler.py --output afp_topics.json
python3 afp_topics_to_csv.py --input afp_topics.json --output afp_topics.csv
```

## CSV format

`afp_topics.csv` contains one row per topic-entry assignment from `afp_topics.json`.

- `id`: the AFP entry filename without the `.html` extension.
- `topic1`, `topic2`, `topic3`: the topic hierarchy extracted from the AFP page title.
- `published_year`: the year heading shown for the entry on the AFP topic page.

For example, the entry URL `https://www.isa-afp.org/entries/Dynamic_Pushdown_Networks.html` becomes the CSV id `Dynamic_Pushdown_Networks`.

## Metadata merge

To enrich another metadata CSV, merge on `id` and add the AFP topics as `domain_cluster1`, `domain_cluster2`, and `domain_cluster3`:

```bash
python3 merge_afp_topics_into_metadata.py \
  --metadata-csv theories_metadata.csv \
  --topics-csv afp_topics.csv \
  --output theories_metadata_with_topics.csv
```

Before merging, the script deduplicates `afp_topics.csv` by `id`. If an entry appears multiple times, it keeps the row with the deepest topic assignment (most non-empty topic columns); ties are resolved by keeping the later row in the CSV. The merge also fills `published_year` from the AFP topics CSV, while preserving any existing value when no topic match is found. The CSV reader also raises the parser field-size limit so very large metadata columns can be loaded safely.

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
  - the list of AFP entry URLs and their published years.

## Notes

- The tools use only the Python standard library.
- Entry URLs are normalized to absolute `https://www.isa-afp.org/entries/...html` links.
- Duplicate entry links on a topic page are removed while preserving page order.
- The CSV keeps the AFP topic labels exactly as they appear in the topic page titles.
