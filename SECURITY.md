# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub's
[private vulnerability reporting](https://github.com/soheil-mp/wingbeat/security/advisories/new)
instead of opening a public issue. Include the affected component, version or commit, and steps
to reproduce with synthetic data. You can expect an acknowledgement within 7 days.

## Supported versions

Until 1.0, only the latest release and `main` receive fixes.

## Scope notes

- Devices authenticate to the MQTT broker with per-device credentials over TLS. Reports about
  weaknesses in that path are especially welcome.
- The public API is read-only; admin endpoints require a token from the environment.
- Wingbeat never stores raw audio or personal data by design. A path that leaks either counts
  as a security issue.
