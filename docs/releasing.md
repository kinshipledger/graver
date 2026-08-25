# Maintainer release process

graver uses Conventional Commit pull-request titles, squash merges, and a manually
triggered Release Please workflow. Release Please is the sole mechanism for updating
the package version, finalizing the changelog section, creating the Git tag, and
creating the GitHub Release.

## Release-candidate entry gate

Before requesting `1.0.0rc1`, confirm:

- the supported CLI, Python API, JSON, configuration, and database contracts are
  documented and tested;
- migration tests cover every recognized older schema, backup collision, rollback,
  newer/unknown refusal, integrity, and foreign keys;
- the researcher tutorial and installed-wheel consumer workflow pass offline;
- Python 3.11 through 3.14, macOS, and the Windows portability contract pass;
- branch coverage remains at or above the documented floor;
- no known dependency vulnerability remains without a written risk decision;
- release notes identify user changes, developer changes, breaking changes,
  migrations, security implications, known limitations, and deferred scope;
- professional-researcher review gates required for implemented evidence behavior
  have passed; and
- the private critical-path review shows no unacknowledged scope creep.

Do not migrate the only copy of a research database for release validation. Use
generated fixtures, sanitized purpose-built migration fixtures, or explicitly
authorized temporary copies.

## Prepare the release

1. Start from a clean, synchronized `main` branch.
2. Review `CHANGELOG.md` and the draft release notes. Rewrite mechanical commit
   summaries into meaningful researcher-facing and developer-facing language.
3. Run the complete locked local validation documented in `CONTRIBUTING.md`.
4. In a separate reviewed configuration pull request, enable Release Please's
   prerelease versioning, `rc` prerelease type, and GitHub prerelease flag. Do not
   leave a one-time forced version in permanent configuration.
5. Dry-run the exact Release Please configuration and confirm that its Python update
   produces the intended first candidate version, `1.0.0rc1` in normalized PEP 440
   form. Stop if it proposes an ordinary release, a `0.x` release, or a different
   candidate number.
6. Merge that configuration only after the dry run is correct, then trigger the
   **Release Please** workflow manually.
7. Review the generated release pull request. Confirm the package version has no
   leading `v`; the Git tag may use `v`, and the GitHub Release must be marked as a
   prerelease.
8. Require the ordinary pull-request checks to pass before merging.

Merging the release pull request is the deliberate publication decision. Do not
merge merely because automation generated it.

## Validate the release artifact

Before announcing the release candidate, verify from the built wheel or published
artifact—not the source tree—that:

- `graver --version` and `python -m graver --version` agree;
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
- Open follow-up issues for accepted limitations rather than hiding them in chat or
  local notes.
- Keep prerelease feedback separate from promises for `1.0.0`; evaluate findings
  against data safety, provenance, public-contract compatibility, and scope.
- Do not delete migration support merely because the release succeeded.
