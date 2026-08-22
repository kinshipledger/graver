# Access and acquisition policy

Reviewed: 2026-08-21

This document governs acquisition behavior in project-maintained graver code and
accepted contributions. It is a conservative project policy, not legal advice. It
cannot guarantee or control every downstream modification or user action.

graver supports responsible, researcher-directed acquisition and
provider-authorized data workflows. Researchers remain responsible for applicable
law, provider terms, robots policies, and access instructions. Public availability
of data does not by itself authorize systematic retrieval or redistribution.

## Authorization comes first

Prefer official APIs, authorized exports and imports, licensed datasets, and
researcher-supplied files whose use is permitted. Each provider and operation needs
an explicit enablement decision. Ordinary researcher-directed operations remain
subject to the provider's current terms and access policies.

Operational controls do not create authorization. Throttling, request spacing or
jitter, retry limits, exponential backoff, bounded `Retry-After`, request budgets,
quiet hours, scheduling, and resumability are resource-management and reliability
safeguards used only after an authorization basis exists. No request rate is
inherently acceptable.

The conventional Requests-backed transport improves graver's architecture and
alignment with this policy, but it does not authorize access. Unattended Find a
Grave full-record acquisition remains disabled until a documented authorization
basis permits it. The [Ancestry Terms and
Conditions](https://www.ancestry.com/c/legal/termsandconditions) and
[Ancestry Community Rules](https://www.ancestry.com/c/legal/community-rules) were
reviewed on 2026-08-21. They cover Find a Grave and inform this conservative
unattended-acquisition policy; this statement is not a definitive legal
interpretation.

## Fail-closed access behavior

Current acquisition stops immediately on HTTP `403` and on a recognized access-
challenge response. Challenge recognition is necessarily limited: any unexpected
access response requires human review and must not trigger automated circumvention.
One bounded retry may occur for HTTP `429`; a repeated `429` stops for human review,
and `Retry-After` is bounded rather than followed without limit. Transport and
parsing failures are reported instead of bypassed.

Any future provider-governed unattended job must pause for CAPTCHA or challenge
responses, access denial, authentication changes, repeated rate limiting, changed
provider policy, or policy uncertainty. It must use provider-specific budgets and
stop conditions, bounded retries, auditable outcomes, and explicit cancellation.

## Prohibited behavior and contributions

graver will not implement or accept contributions intended to provide:

- CAPTCHA or automated challenge solving;
- browser or TLS fingerprint manipulation;
- stealth or human-impersonation modes;
- proxy rotation intended to evade restrictions or conceal activity;
- credential or cookie sharing;
- access-control bypass or concealment of automated activity; or
- unauthorized systematic downloading.

Incidental ordinary proxy support in a general-purpose HTTP library is not itself
prohibited. Using proxy infrastructure to evade provider restrictions or conceal
activity is prohibited.

## Gate for unattended provider adapters

Before implementing or enabling a provider-specific unattended adapter, the project
must:

1. Identify the provider and intended operation.
2. Perform and record a dated review of current terms and technical documentation.
3. Document the authorization basis.
4. Obtain maintainer approval and seek qualified legal review when the intended use
   is materially uncertain.
5. Define provider-specific budgets, pause conditions, and stop conditions.
6. Provide mocked offline contract tests.

Live contract probes remain separate, minimal, explicitly invoked, and incapable of
bulk behavior. Ordinary automated tests must not contact providers. Authorization
records, review dates, and relevant policy links must be retained and rechecked
before provider integration and applicable releases.

Import-first acquisition from authorized sources should precede unattended live
retrieval. Provider-neutral queues, scheduling, resumability, and GUI/CLI progress
are planned architecture only; graver currently has no background-job engine,
scheduler, import service, or unattended full-record acquisition mode.
