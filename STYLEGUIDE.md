# Graver documentation style guide

This guide defines the editorial and Markdown conventions enforced in Graver's
maintained public documentation. The [visual identity guide](docs/visual-identity.md)
remains authoritative for brand meaning, product relationships, and visual assets.
The [contribution guide](CONTRIBUTING.md) explains how to run the checks.

## Project and identifier names

Use **Graver** for the open-source project and research engine. Use **Kinship
Ledger** for the publisher, broader product family, and later professional
researcher application.

Use inline code for the literal `graver` command, Python import root, namespace,
package identifier, or another exact machine value. For example:

- Graver preserves dated source observations.
- Run `graver --version` to inspect the installed command.
- Import the supported interface from `graver.application`.
- Install the `graver-genealogy` distribution.
- Visit the `kinshipledger/graver` repository.

Bare lowercase `graver` without code styling is not valid ordinary prose. The
linter can identify that lexical form, but a human reviewer remains responsible for
deciding which referent the sentence actually means.

## Sentence-case headings

Use sentence case for every heading in maintained, project-authored Markdown:

- Capitalize the first ordinary word.
- Lowercase later ordinary words.
- Preserve canonical capitalization for proper names, acronyms, standards, and
  code identifiers.
- Put commands, imports, filenames, and machine identifiers in inline code.
- Preserve a question mark when the heading is a question; otherwise omit trailing
  punctuation.

Preferred examples:

```markdown
# Graver documentation style guide
## Install Graver
## Run `graver`
## Configure the SQLite database
## FamilySearch candidate discovery
## What does Graver retain?
```

## Enforced scope

[`docs/documentation-scope.json`](docs/documentation-scope.json) classifies every
tracked Markdown file exactly once. New Markdown is treated as maintained prose and
fails validation until it receives an explicit classification.

Current project-authored documentation and maintained templates are enforced.
Generated release history, upstream-governed text, dated review evidence, and
deliberately failing fixtures are excluded only through exact entries that explain
their provenance and review trigger. Exclusion protects accepted or generated
wording; it does not weaken review of current documentation.

## Automated enforcement

Vale 3.22.0 enforces deterministic heading and terminology rules stored under
`styles/Graver/`. Vale checks lexical and structural consistency; it does not certify
semantic accuracy, evidence meaning, accessibility, or factual correctness.

The official Vale pre-commit hook is pinned to the immutable source commit for
release 3.22.0, `e109c06297dc58a513f10691a275f3a9465584a1`. Its first run downloads
and builds the hook in pre-commit's isolated cache. The source-built executable
reports its development label rather than the release tag, so the checker verifies
the exact official repository and commit pin separately from the executable-response
canary. Later runs use the cache and must work without network access.

Run the complete cross-platform check with:

```shell
uv run python maintenance/check_documentation_style.py
```

On systems with Make, `make stylecheck` is an equivalent convenience command.
Required CI runs the same checker. A successful result means only that every tracked
Markdown file is classified, the pinned Vale version and rule fixtures behave as
expected, and the enforced corpus has no error-level findings.

## Exceptions and changes

Keep exclusions and terminology exceptions in checked-in configuration. Each
exception must identify the narrowest affected scope, its rule or category, its
reason and owner, and a review or removal trigger. Broad inline `vale off` regions
are prohibited. A local suppression is acceptable only when the visible source must
preserve exceptional wording and the nearby comment explains why.

The project maintainer owns Vale upgrades. Upgrade the hook manually and review both
fixture and full-corpus output before accepting the change. Do not automatically
rewrite prose merely to satisfy a changed linter result.

If Vale becomes unavailable or produces disproportionate false positives, retain
this policy and its last accepted configuration while disabling the failing
mechanism in a repair pull request. Restore required enforcement only after a green,
bounded canary.
