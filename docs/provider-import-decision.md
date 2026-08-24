# Provider acquisition and import decision

Decision date: 2026-08-24
Status: Approved pre-1.0 scope gate

This record applies the [access policy](access-policy.md) to the acquisition and
import work considered for `1.0.0rc1`. It is a conservative product and engineering
decision, not legal advice or a claim that any particular use is legally permitted.

## Decision

graver will retain its bounded, researcher-directed Find a Grave operations:

- one explicitly submitted summary search; and
- one full-record enrichment for a memorial whose research task the researcher has
  explicitly approved.

These operations remain fail-closed and subject to the provider's current terms,
technical controls, and the researcher's responsibilities. Their presence does not
create permission for systematic collection.

graver will **not** implement or enable unattended, scheduled, or background Find a
Grave acquisition for `1.0.0rc1`. The project has no documented official API,
written permission, licensed dataset, or other authorization basis for that
operation. Request spacing, jitter, budgets, and retries would not cure that gap.

graver will also defer a public background-job engine and public import API until a
concrete, authorized workflow needs them. Freezing provider-neutral abstractions in
the absence of a permitted adapter would create speculative compatibility rather
than user value. This deferral does not prevent the current database upgrade path,
offline fixtures, or later imports from researcher-supplied files that the
researcher is authorized to use.

## Dated provider review

The maintainer reviewed the current
[Ancestry Terms and Conditions](https://www.ancestry.com/c/legal/termsandconditions)
and
[Ancestry Community Rules](https://www.ancestry.com/c/legal/community-rules)
on 2026-08-24. The Terms identify Find a Grave as an Ancestry service, permit use
for personal or professional family-history research, and limit downloading and
programmatic access. In particular, they prohibit manual, automated, or
programmatic access that exceeds intended standard human use. The current Terms
show an effective date of 2026-05-12.

No official Find a Grave bulk-acquisition API, export mechanism for the contemplated
operation, or written project permission was identified in this review. Absence of
such evidence is treated as a failed authorization gate, not as implied permission.

## Operation decisions

| Operation | Pre-1.0 decision | Reason and guardrail |
|---|---|---|
| Researcher submits one narrow summary search | Retain conditionally | Explicit user action, bounded request, transparent transport, and fail-closed access behavior. Stop if provider policy or controls indicate the operation is not permitted. |
| Researcher approves and enriches one memorial | Retain conditionally | One named memorial, durable approval state, one acquisition attempt, immutable acquisition observation and provenance, and no automatic continuation. |
| Minimal live canary | Retain as a separate maintenance probe | Explicit invocation, one stable memorial, no bulk behavior, and immediate stop on restriction. It is never part of the ordinary automated suite. |
| Unattended or scheduled Find a Grave acquisition | Do not implement or enable | No documented authorization basis. Operational throttling cannot substitute for permission. |
| Generic public background-job API | Defer beyond rc1 | No authorized provider adapter currently justifies freezing a public contract. Revisit from a concrete workflow. |
| Researcher-supplied local file | Eligible for later consideration | The researcher must have the right to use it. Import must be offline, explicit, provenance-preserving, transactional, and source-labeled. No rc1 feature is required. |
| Official export, documented API, or licensed dataset | Eligible after its own gate | Record provider/format, permission basis, allowed operations, attribution, redistribution limits, review date, budgets, and offline contract tests before implementation. |
| GEDCOM | Remains optional and deferred | Re-evaluate against demonstrated research value; it is not an rc1 criterion or a shortcut around provider restrictions. |

## Required invariants

The following remain non-negotiable across future adapters:

- imports never imply that source assertions are true or that two identities match;
- every imported observation identifies its represented source, access surface,
  capture scope, and import event;
- prior observations are retained rather than rewritten;
- dry-run or validation occurs before mutation when practical;
- a failed batch is atomic or reports explicit durable partial progress by design;
- imports perform no hidden network access;
- live adapters use typed progress, cancellation, bounded failures, and provider-
  specific authorization records;
- CAPTCHA, access challenges, `403`, repeated `429`, or policy uncertainty stop for
  human review; and
- no adapter circumvents, conceals, or misrepresents its activity.

## Reopening this decision

The unattended-provider or public-job decision may be reopened only when at least
one of these exists:

1. a documented official API or export that permits the intended operation;
2. written provider permission;
3. a licensed dataset with compatible rights; or
4. another concrete, reviewed authorization basis.

Reopening requires a new dated terms and technical review, maintainer approval,
provider-specific limits and stop conditions, offline contract tests, and qualified
legal review when material uncertainty remains. Until then, background acquisition
and its scheduler are post-1.0 non-goals.

## Release effect

`1.0.0rc1` does not require a job engine, scheduler, general import command, GEDCOM
adapter, or unattended provider integration. It does require that all retained live
acquisition continue through the typed application boundary, remain bounded and
researcher-directed, and comply with the access policy. That acquisition-service
parity was completed before this decision.
