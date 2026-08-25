# Security policy

## Supported versions

graver has not yet published a supported production release. Security fixes are
made on `main` during pre-1.0 development. Supported-version details will be added
before the first release candidate.

The current application is a local, single-researcher CLI with no telemetry,
accounts, or hosted synchronization. Its boundaries and residual risks are
documented in the [security threat model](docs/security-threat-model.md), and its
local data behavior is documented in [privacy and data handling](docs/privacy-and-data-handling.md).

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's
private vulnerability-reporting feature from the repository's **Security** tab.
Include the affected version or commit, impact, reproduction details, and any known
mitigation. If private reporting is unavailable, contact `contact@mcqueary.org`.

Do not include credentials, cookies, private genealogy data, or other sensitive
material in reports unless a secure exchange method has been agreed upon.

Expected malformed-input, provider-blocking, or ordinary configuration errors are
not usually security vulnerabilities. Reports are especially helpful when they
show unauthorized disclosure or modification, traversal outside a selected path,
injection, unsafe archive/import handling, credential exposure, dependency or
release compromise, or a way to bypass provenance and decision-history controls.
