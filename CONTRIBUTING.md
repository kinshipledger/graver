# Contributing to graver

Thank you for helping improve graver. Please read the
[access policy](docs/access-policy.md) before proposing acquisition or provider
integration changes. Participation in project spaces is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Development workflow

`main` is the only long-lived branch. Create a short-lived branch from current
`main`, keep the change focused, and open a pull request back to `main`. Pull
requests are squash-merged after required checks pass, so the pull-request title
becomes the permanent commit subject.

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for pull-
request titles:

```text
feat(cli): add database selection
fix(db): preserve task timestamps during upgrade
docs: clarify the researcher workflow
```

Supported types are `build`, `chore`, `ci`, `deps`, `docs`, `feat`, `fix`, `perf`,
`refactor`, `revert`, `security`, and `test`. Add `!` before the colon for an
intentional breaking change and explain it in the pull-request body.

AI-assisted contributions are welcome under the same standards as any other
contribution. The contributor remains responsible for understanding the change,
its licensing and provenance, its tests, and every statement made in the pull
request. Do not give an external assistant credentials, private genealogy data, or
other material that is not appropriate to disclose. Assistance does not substitute
for human review of evidence meaning, security, or data-preservation behavior.

## Local validation

Install the locked environment and run the offline checks:

```shell
uv sync --locked --group test --group dev
uv run pre-commit install
uv run pre-commit run --all-files
uv run --group dev pip-audit
uv run --group dev ruff check --select S --ignore S608 src/graver maintenance
uv run pytest
uv run pytest --cov=graver --cov-report=term-missing --cov-report=xml
uv lock --check
```

These commands are the cross-platform validation path and do not require an
activated virtual environment. On systems with a compatible `make` installation,
`make lint`, `make security`, `make typecheck`, and `make doccheck` are equivalent
convenience shortcuts for the corresponding static and security checks. GNU Make
is an external system tool and is not installed by uv or required by graver.

`make lint` runs the required Black formatting check and Ruff lint/import-order
check over production, test, review, consumer-spike, and benchmark Python. `make
security` checks locked dependencies for published vulnerabilities and runs Ruff's
production security rules. Its documented S608 exclusion covers manually reviewed
SQL assembled only from fixed internal identifiers; values must remain parameter-
bound. CodeQL independently analyzes pull requests and `main`. `make typecheck`
runs mypy over the
supported application boundary in `graver.application`, `graver.database`,
`graver.evidence`, and `graver.research`. `make doccheck` enforces Google-style
public docstring coverage over that same boundary, excluding redundant magic-method
and constructor docstrings where the class contract already carries the meaning.
The installed pre-commit hooks run the same checks. CI is authoritative and repeats
the full required scope.

The first test command is the ordinary fast suite. The second reproduces the
dedicated CI branch-coverage measurement and should be run when behavior or tests
change. Coverage is reported from one Ubuntu/Python lane rather than duplicated
across every supported Python and operating-system lane. That coverage lane is also
the complete Python 3.14 test lane; Python 3.11–3.13 run the ordinary suite
separately. macOS runs the complete suite, while Windows runs the portability-focused
database, configuration, entry-point, workspace, error, progress, and public-contract
tests because its full fixture-heavy suite is disproportionately slow without adding
equivalent platform evidence.

Pytest disables socket access for the entire ordinary suite. Tests that consume the
existing sanitized provider cassettes are marked `recorded` automatically and run in
replay-only mode; a missing interaction fails instead of contacting the provider.
Use `uv run pytest -m recorded` to run that contract layer alone. The registered
`unit`, `integration`, `recorded`, and `slow` markers are checked strictly. Recording
or refreshing provider fixtures is a separate, explicitly authorized maintainer
activity—not part of an ordinary test run or pull request.

Required CI jobs have a five-minute ceiling and should normally provide pull-request
feedback in under four minutes. Review the workflow when a required job exceeds four
minutes, its duration grows by 25 percent across comparable runs, or a proposed test
substantially duplicates an existing lane. Optimize fixtures and lane responsibilities
before weakening assertions; platform-specific or live checks need an explicit reason
and bounded fallback. Test count is useful context, not a goal by itself.

The optional `make performance` shortcut runs the informational offline workspace
baseline with generated 100- and 10,000-record databases. It is not a required
pull-request gate and its wall-clock results should not be compared across unlike
machines. A direct uv command is documented in the [performance and responsiveness
guide](docs/performance.md). The separate weekly/manual workflow retains JSON
reports for trend review.

SQLite `ResourceWarning`s
and unraisable finalizer warnings fail pytest so connection leaks cannot quietly
return.

Mypy is intentionally enforced incrementally at the public application boundary;
untyped legacy parser and CLI internals are not silently represented as checked.
Unused-code removal requires corroborating Ruff, repository-reference, test,
coverage, export, and compatibility evidence. No heuristic dead-code detector is a
required project tool.

Public application imports and stability expectations are documented in the
[developer API guide](docs/api.md). New client-facing behavior belongs behind that
typed boundary; do not expose SQLite, Typer, terminal-rendering, Requests, or parser
implementation objects through it.

Tests and ordinary CI must not contact genealogy providers. Use temporary databases
and configuration paths; never commit research databases, credentials, cookies,
logs, cassettes containing sensitive data, or local configuration.
Put disposable JSON and other researcher-generated exports under `scratch/` or
`exports/`; both directories are ignored without hiding legitimate project JSON.

## Releases

[Release Please](https://github.com/googleapis/release-please) is the sole tool for
preparing versions, changelog sections, tags, and GitHub Releases. Its workflow is
manual while graver is pre-1.0. A maintainer reviews the generated release pull
request for meaningful user and developer notes before merging it. Package-index
publication uses a separate OIDC trusted-publishing job in that manually triggered
workflow; the release-candidate package is published as `graver-genealogy` while the
command and import package remain `graver`.

## Project name and terminology

The canonical project name is **graver**, styled in lowercase even at the start
of a sentence. Use backticks when referring to the literal command, package,
module, or another code identifier—for example, `graver init`—but ordinary prose
does not need code styling simply because it names graver.

The name graver covers the research engine, core library, application services, and
command-line tool. Kinship Ledger is the broader project and publishing context.
The future professional desktop application is a separate product layer and may
have a separate name; do not assume or establish that name in graver documentation
before it is chosen.

## Documentation voice

Write for the reader's immediate goal before introducing implementation or roadmap
detail. Prefer plain, warm, direct language; define necessary genealogy and software
terms, and move specialist material behind clear links or advanced command groups.
Claims must distinguish current behavior from planned work and must not overstate
evidence, identity, provenance, provider authorization, or data completeness.

Prefer functional-role names in researcher-facing headings, diagrams, navigation,
and concepts: name what something helps the researcher do before naming the module,
storage mechanism, framework, or internal status that implements it. Preserve exact
commands and stable machine values in secondary detail when readers need them for
operation, troubleshooting, automation, or compatibility.

Occasional restrained humor, wordplay, or self-awareness is welcome when it makes
an unfamiliar workflow feel more approachable. Keep it sparse and never use it to
trivialize research evidence, living-person privacy, data loss, failures, security,
legal obligations, or provider access restrictions. Clarity and trust always win
the tie.
