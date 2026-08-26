# Security policy

## Supported versions

graver has published `1.0.0rc1` for release-candidate testing. Security fixes are
developed on `main`; a reported vulnerability is assessed for a corrected
prerelease when it affects the published candidate. Versions older than the latest
published prerelease are not maintained as separate supported lines during pre-1.0
development. The stable-version support policy will be defined for final 1.0.

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
