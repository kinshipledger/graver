# Contributing to graver

Thank you for helping improve graver. Please read the
[access policy](docs/access-policy.md) before proposing acquisition or provider
integration changes.

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

## Local validation

Install the locked environment and run the offline checks:

```shell
uv sync --locked --group test --group dev
uv run pytest
uv run pytest --cov=graver --cov-report=term-missing --cov-report=xml
uv run black --check src/graver tests
uv lock --check
```

The first test command is the ordinary fast suite. The second reproduces the
dedicated CI branch-coverage measurement and should be run when behavior or tests
change. Coverage is reported from one Ubuntu/Python lane rather than duplicated
across every supported Python and operating-system lane.

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
publication, if later added, is a separate trusted workflow.

## Project name and terminology

The canonical project name is **graver**, styled in lowercase even at the start
of a sentence. Use backticks when referring to the literal command, package,
module, or another code identifier—for example, `graver init`—but ordinary prose
does not need code styling simply because it names graver.

The name graver covers the core library, application services, and command-line
tool. Cemetery-to-World-Tree is the broader project context. A future desktop
application may have a separate product name; do not assume or establish that
name in graver documentation before it is chosen.

## Documentation voice

Write for the reader's immediate goal before introducing implementation or roadmap
detail. Prefer plain, warm, direct language; define necessary genealogy and software
terms, and move specialist material behind clear links or advanced command groups.
Claims must distinguish current behavior from planned work and must not overstate
evidence, identity, provenance, provider authorization, or data completeness.

Occasional restrained humor, wordplay, or self-awareness is welcome when it makes
an unfamiliar workflow feel more approachable. Keep it sparse and never use it to
trivialize research evidence, living-person privacy, data loss, failures, security,
legal obligations, or provider access restrictions. Clarity and trust always win
the tie.
