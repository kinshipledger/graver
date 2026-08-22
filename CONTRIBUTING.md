# Contributing to Graver

Thank you for helping improve Graver. Please read the
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
uv run black --check src/graver tests
uv lock --check
```

Tests and ordinary CI must not contact genealogy providers. Use temporary databases
and configuration paths; never commit research databases, credentials, cookies,
logs, cassettes containing sensitive data, or local configuration.

## Releases

[Release Please](https://github.com/googleapis/release-please) is the sole tool for
preparing versions, changelog sections, tags, and GitHub Releases. Its workflow is
manual while Graver is pre-1.0. A maintainer reviews the generated release pull
request for meaningful user and developer notes before merging it. Package-index
publication, if later added, is a separate trusted workflow.
