# Live compatibility canary

graver's ordinary test suite is deliberately offline. Recorded fixtures tell us
whether known page representations still parse; they cannot tell us whether the
provider's current public page still satisfies the same minimum contract.

The live canary answers that narrow question for maintainers. It retrieves the
designated public George Washington memorial, parses it with graver's default
Requests transport and current memorial parser, and reports whether the expected
identity and burial linkage remain recognizable.

## Run it deliberately

From a source checkout with synchronized dependencies:

```shell
make canary
```

For a versioned, machine-readable result:

```shell
make canary-json
```

Both commands make a real request to Find a Grave. Run them manually before a
release or after a material parser or transport change—not as part of routine local
tests, pull-request checks, or unattended scheduled CI. Review the
[access policy](access-policy.md) before use.

## Safety boundary

Each invocation:

- targets only `https://www.findagrave.com/memorial/1075/george-washington`;
- permits exactly one top-level request attempt and disables graver retries;
- uses short, explicit connection and read timeouts;
- uses no authentication and reads no user configuration;
- creates or changes no research database;
- stops when access is denied or challenged;
- never solves a challenge, rotates a proxy, or refreshes a recorded fixture; and
- reports a response hash and limited structural metadata, never response content,
  cookies, credentials, or provider control identifiers.

An ordinary HTTP redirect is reported separately. It may involve another HTTP
exchange inside Requests, but the probe never initiates a second acquisition
attempt.

## Interpret the result

The exit status is zero only for `compatible`. Other categories are diagnostic and
must be reviewed rather than automatically treated as unrelated release failures.

| Category | Meaning |
|---|---|
| `compatible` | The transport and parser recognized the expected memorial and burial linkage. |
| `schema_changed` | The page was obtained but required semantic fields did not parse, or parsing failed unexpectedly. |
| `access_blocked` | The provider denied or challenged access; stop and review. |
| `site_unavailable` | The provider could not be reached within the bounded attempt. |
| `canary_changed` | Parsing succeeded, but stable identity values for the designated memorial changed. |
| `probe_error` | The maintenance harness itself failed or encountered an unclassified condition. |

A successful result is a compatibility signal, not permission for broader access
and not proof that every provider page shape remains compatible. A failure should
be classified before changing code, fixtures, release status, or provider policy.

## Development and verification

The probe's automated tests inject local responses and run under the repository's
network-denying pytest policy. The ordinary `make test` target never invokes the
live canary. Do not add `make canary` to continuous-integration or release workflows
without a separate, dated provider-policy review and maintainer decision.
