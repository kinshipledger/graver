## Description

<!-- Explain what changed, why it is needed, and the user-visible or technical
outcome. Keep implementation detail proportional to the review risk. -->

## Related issues

<!-- Use `Closes #123`, `Fixes #123`, or `Related to #123` where appropriate. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor with no intended behavior change
- [ ] Documentation
- [ ] Tests or developer tooling
- [ ] Database schema or migration
- [ ] Breaking change

## How was this validated?

<!-- List exact validation categories and meaningful manual scenarios. Explain any
relevant check that was intentionally skipped. Tests must remain offline unless the
change is an explicitly authorized live-contract probe. -->

- [ ] Focused tests
- [ ] Complete offline test suite
- [ ] Formatting/static checks applicable to the change
- [ ] Documentation links and examples
- [ ] Database integrity, migration, or rollback checks
- [ ] Installed-wheel or public-API verification
- [ ] Manual researcher workflow
- [ ] Not applicable; explanation provided below

## User experience evidence

<!-- For visible changes, include concise before/after output, screenshots, or a
workflow description. Remove this section only when the change has no visible
effect. Do not include private research data, credentials, cookies, or unsanitized
provider responses. -->

## Professional-researcher semantic impact

Does this change affect researcher-visible terminology, evidence meaning, candidate
ranking, identity conclusions, citations, provenance, or workflow continuity?

- [ ] No
- [ ] Yes — relevant professional-researcher review gate or issue:

If **Yes**, explain whether the change is queued for the next review gate, resolves a
recorded finding, or requires a new blocking review. Do not mark a gate complete
merely because this pull request updates plans, tests, or documentation.

## Data, compatibility, security, and external services

- [ ] No database schema or migration impact
- [ ] Existing research data and provenance are preserved and recovery is documented
- [ ] No public CLI, Python API, JSON, configuration, or file-format compatibility impact
- [ ] Compatibility or migration impact is documented
- [ ] No new secret, credential, personal-data, or logging exposure
- [ ] External-provider access remains within `docs/access-policy.md`
- [ ] Not applicable; explanation provided below

## Documentation and release notes

- [ ] User and developer documentation is updated where needed
- [ ] User-facing, developer-facing, migration, security, or breaking-change notes are included where needed
- [ ] No documentation or release-note change is required

## Final checklist

- [ ] The PR title follows Conventional Commits
- [ ] The change is focused and contains no unrelated files
- [ ] Tests demonstrate the behavior or the omission is justified
- [ ] Generated artifacts, research databases, credentials, and local configuration are not included
- [ ] I reviewed the diff for misleading current-state or roadmap claims
