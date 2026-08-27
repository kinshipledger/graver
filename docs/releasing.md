# Maintainer release process

graver uses Conventional Commit pull-request titles, squash merges, and a manually
triggered Release Please workflow. Release Please is the sole mechanism for updating
the package version, finalizing the changelog section, creating the Git tag, and
creating the GitHub Release. The same workflow builds and tests the tagged source
archive and wheel, then publishes them to PyPI through Trusted Publishing. The build
job has no publishing credential; the publishing job receives only an ephemeral OIDC
identity.

## Release gate

Before requesting another candidate or the final `1.0.0` release, confirm:

- the supported CLI, Python API, JSON, configuration, and database contracts are
  documented and tested;
- migration tests cover every recognized older schema, backup collision, rollback,
  newer/unknown refusal, integrity, and foreign keys;
- the researcher tutorial and installed-wheel consumer workflow pass offline;
- Python 3.11 through 3.14, macOS, and the Windows portability contract pass;
- branch coverage remains at or above the documented floor;
- the required CI dependency audit and production security-rule checks pass, and no
  known vulnerability remains without a written risk decision;
- release notes identify user changes, developer changes, breaking changes,
  migrations, security implications, known limitations, and deferred scope;
- professional-researcher review gates required for implemented evidence behavior
  have passed; and
- researcher-facing icons, diagrams, screenshots, badges, and version labels match
  current behavior, have recorded provenance, and pass their applicable light/dark,
  small-size, text-alternative, professional, and accessibility reviews; and
- the private critical-path review shows no unacknowledged scope creep.

The public distribution name is `graver-genealogy`; the product, console command,
and import package remain `graver`. PyPI's `graver` project is unrelated. Verify the
built metadata and every installation example against this distinction.

The protected GitHub environment `pypi` and PyPI Trusted Publisher must match the
current repository owner, repository `graver`, workflow `release-please.yml`, and
environment `pypi`. Re-verify this binding after an organization transfer. Never add
a long-lived PyPI token as a repository secret.

Do not migrate the only copy of a research database for release validation. Use
generated fixtures, sanitized purpose-built migration fixtures, or explicitly
authorized temporary copies.

## Prepare the release

1. Start from a clean, synchronized `main` branch.
2. Review `CHANGELOG.md` and the draft release notes. Rewrite mechanical commit
   summaries into meaningful researcher-facing and developer-facing language.
3. Run the complete locked local validation documented in `CONTRIBUTING.md`.
   Run `make release-check` to test both publishable artifact forms outside the
   source tree.
4. Review the checked-in Release Please configuration and manifest. Confirm the
   intended prerelease or ordinary-release mode, and do not add a one-time forced
   version to routine release configuration.
5. Trigger the **Release Please** workflow manually and review the generated release
   pull request. Stop if it proposes an unexpected release line or candidate number.
6. Confirm the package version has no
   leading `v`; the Git tag may use `v`, and the GitHub Release must be marked as a
   prerelease when appropriate.
7. Require the ordinary pull-request checks to pass before merging.

Merging the release pull request and then deliberately running the Release Please
workflow is the publication decision. A newly created release causes the workflow's
isolated build and PyPI jobs to run. Do not merge or trigger publication merely
because automation generated the pull request.

## Validate the release artifact

Before announcing the release candidate, verify from the built wheel or published
artifact—not the source tree—that:

- `graver --version` and `python -m graver --version` agree;
- installed distribution metadata reports `graver-genealogy` while the command and
  import package remain `graver`;
- `graver --help` and the documented command hierarchy work;
- `graver init`, `use`, read-only inspection, and explicit upgrade behave as
  documented in isolated paths;
- a generated legacy database upgrades through the verified-backup workflow;
- the tutorial's offline steps and injected consumer workflow remain valid; and
- `graver.application` exposes only the documented public names.

Record supported-platform results and any accepted limitation in the GitHub Release.
Never use live bulk acquisition as a release check. A separately authorized minimal
provider canary may validate transport/parser compatibility without becoming a
release automation dependency.

## After release

- Confirm the tag, GitHub Release, changelog links, and install instructions resolve.
- Confirm the `graver-genealogy` PyPI page, wheel, source archive, and attestations
  are present and correspond to the GitHub tag.
- Open follow-up issues for accepted limitations rather than hiding them in chat or
  local notes.
- Keep prerelease feedback separate from promises for `1.0.0`; evaluate findings
  against data safety, provenance, public-contract compatibility, and scope.
- Do not delete migration support merely because the release succeeded.

## Historical first-candidate bootstrap

The first supported candidate, `1.0.0rc1`, required a one-time reviewed Release
Please bootstrap because the repository previously tracked development versions.
That procedure temporarily used `release-as: 1.0.0-rc.1`, verified that Release
Please proposed normalized Python version `1.0.0rc1` and Git tag
`v1.0.0-rc.1`, and removed the forced value on the generated release branch before
publication. The release manifest now records the published state. Do not repeat
this bootstrap for later candidates or `1.0.0` unless a separately reviewed recovery
plan establishes that the manifest is incorrect.
