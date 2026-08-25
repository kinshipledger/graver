# Pre-1.0 command-line migration

graver intentionally removed its hidden compatibility commands and normalized the
Find a Grave search options before freezing the 1.0 CLI. This page maps the removed
spellings to the supported researcher-facing interface.

## Command replacements

| Removed command | Supported replacement |
| --- | --- |
| `queue-memorials` | `work queue` |
| `list-tasks` | `work list` |
| `show-task ID` | `work show ID` |
| `update-task ID` | `work mark ID` |
| `scrape-task ID` | `work enrich ID` |
| `list-aliases` | `admin aliases list` |
| `show-alias ID` | `admin aliases show ID` |
| `record-alias SOURCE TARGET` | `admin aliases record SOURCE TARGET` |
| `retract-alias SOURCE` | `admin aliases retract SOURCE` |
| `scrape-url` | `search`, followed by `work queue`, explicit approval, and `work enrich ID` |
| `scrape-file` | No unattended replacement; use the reviewed person-at-a-time workflow |

The supported commands use the versioned JSON envelope documented in
[Command-line JSON contract](cli-json.md). Previous result fields are under `data`.

## Search-option replacements

| Removed spelling | Supported spelling |
| --- | --- |
| `--cid` | `--cemetery-id` |
| `--firstname` | `--first-name` |
| `--middlename` | `--middle-name` |
| `--lastname` | `--last-name` |
| `--fulltext` | `--full-text` |
| `--birthyear` | `--birth-year` |
| `--birthyearfilter` | `--birth-year-filter` |
| `--deathyear` | `--death-year` |
| `--deathyearfilter` | `--death-year-filter` |
| `--locationId` | `--location-id` |
| `--id`, `--memorialid` | `--memorial-id` |
| `--mcid` | `--contributor-id` |
| `--bio` | `--biography` |
| `--linkedToName` | `--linked-to-name` |
| `--datefilter` | `--date-filter` |
| `--orderby` | `--order-by` |
| `--noCemetery` | `--no-cemetery` |
| `--isVeteran=true` / `false` | `--veteran` / `--not-veteran` |
| `--includeNickName` | `--include-nickname` |
| `--includeMaidenName` | `--include-maiden-name` |
| `--includeTitles` | `--include-titles` |
| `--exactName` | `--exact-name` |
| `--fuzzyNames` | `--fuzzy-names` |
| `--photofilter` | `--photo-filter` |
| `--gpsfilter` | `--gps-filter` |
| `--hasPlot=true` / `false` | `--has-plot` / `--no-plot` |
| `--max` | `--max-results` |

The remaining former value-taking Boolean filters use the same explicit pattern:

- `--famous` / `--not-famous`
- `--sponsored` / `--not-sponsored`
- `--cenotaph` / `--not-cenotaph`
- `--monument` / `--not-monument`
- `--flowers` / `--no-flowers`

Omitting either side leaves that provider filter unspecified. Use
`graver search --help` as the authoritative list of supported options.
