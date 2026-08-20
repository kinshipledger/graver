# Initial scraper and database inspection

When the existing Python scraper and SQLite database are added, inspect them before proposing implementation changes.

## Scraper

- Entry points, configuration, dependencies, and execution instructions.
- Cemetery and memorial identifiers retained from Find a Grave.
- Pagination strategy, request pacing, retries, caching, and error handling.
- Fields collected, normalization performed, and any information discarded.
- Export behavior and whether SQLite is treated as the primary state store.
- Relevant current access, robots, rate-limit, and terms considerations.

## SQLite database

- Tables, views, indexes, constraints, foreign keys, and schema versioning.
- Row counts and the relationship between cemetery and memorial records.
- Field completeness, type consistency, duplicate patterns, and identifier stability.
- Provenance preservation: distinguish scraped observations from later research conclusions.
- Current task/workflow data, if any.

## Deliverable after inspection

Produce a concise factual inventory and recommend only the smallest architectural changes necessary to support a durable, provenance-preserving research queue. Do not rewrite the scraper solely to match a theoretical model.
