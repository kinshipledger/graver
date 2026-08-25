# Performance and responsiveness

graver tracks a small offline performance baseline so growth in the core application
does not quietly become future desktop-interface sluggishness. The baseline is
observability, not a scorecard: correctness, provenance, and research-data safety
remain more important than shaving milliseconds from synthetic work.

## What is measured

The deterministic harness creates disposable current-schema databases containing
fictional memorial summaries and research tasks. It reports:

- summary-persistence and queue-creation time;
- database file size;
- workspace opening and schema validation time;
- a 50-item work-list query;
- one task-detail query;
- one optimistic-concurrency task update; and
- median, approximate 95th-percentile, and peak traced Python allocation for each
  measured operation.

No research database, user configuration, credential, provider, or network adapter
is used. Generated names and URLs are obviously fictional and carry no genealogical
meaning.

Run the ordinary local baseline with:

```shell
make performance
```

For an occasional capacity probe, explicitly request a larger dataset:

```shell
uv run python benchmarks/performance_baseline.py --sizes 100000 --repetitions 7
```

The larger run is intentionally not part of pull-request CI. Its cost should be
measured before it is added to any recurring workflow.

## Automation and interpretation

The **Performance baseline** GitHub workflow runs weekly and on manual request. It
measures generated 100- and 10,000-record workspaces on one consistent Ubuntu/Python
3.14 lane and retains the versioned JSON report for 90 days. It does not run for
pull requests, contact providers, or fail a change because a shared runner was
temporarily slower.

Compare results only across broadly similar environments. Investigate a sustained
regression, a major algorithmic step change, a database-size jump, or a
researcher-visible delay; do not optimize one noisy sample. Turn a metric into a
required gate only after repeated measurements demonstrate a stable threshold tied
to a real user workflow.

The report's memory value is Python allocation observed by `tracemalloc`, not total
process memory. Provider latency is external-service behavior and is not reported as
graver performance.

## Provisional GUI responsiveness budgets

These are design targets for the future desktop vertical slice, not current release
criteria:

| Interaction | Initial target |
| --- | --- |
| Visible response to input | Within 100 ms |
| Ordinary local operation | Preferably within 250 ms |
| Initial window ready for interaction | Around 1 second or less |
| Progress shown for longer work | Within 250–500 ms |
| Cancellation acknowledged | At the next documented safe boundary, without UI-thread blocking |

Network retrieval and substantial database work must never execute on the GUI
thread. The GUI should translate graver's toolkit-neutral progress and cancellation
contracts into interface state, and measure time-to-interactive, navigation latency,
long-task progress, cancellation, and memory with the real toolkit and representative
workflows.

Review these budgets at the first GUI design spike. Adjust them from user research
and measured hardware rather than treating provisional numbers as universal truth.

## Initial local baseline

The first full run on 2026-08-24 used CPython 3.14.7 on Apple Silicon macOS. These
values establish harness viability, not cross-platform thresholds:

| Metric | 100 records | 10,000 records |
| --- | ---: | ---: |
| Database size | 468 KiB | 21.6 MiB |
| Summary fixture persistence | 95 ms | 9.29 s |
| Queue all records | 10 ms | 680 ms |
| Open and validate workspace (median) | 1.9 ms | 62.9 ms |
| List 50 tasks (median) | 3.7 ms | 79.5 ms |
| Show one task (median) | 2.6 ms | 65.2 ms |
| Update one task | 3.5 ms | 63.7 ms |

The initial 10,000-record run exposed and prompted correction of repeated schema
validation inside an already validated batch transaction. A regression test now
requires one initialization boundary per summary batch. This is precisely the kind
of algorithmic finding the baseline is intended to reveal.
