# Security Controls

## Authentication and authorization

- Custom `User` model uses Django's secure password hashing.
- JWT access tokens are issued by SimpleJWT and expire after 30 minutes.
- Refresh tokens rotate and expire after one day.
- Session authentication supports the server-rendered dashboard with CSRF protection.
- `platform_role` gates administrative, analyst and reviewer actions.
- Organization-scoped querysets prevent cross-workspace reads.
- Anonymous and authenticated API requests are rate limited with configurable thresholds.

## Sensitive data handling

- Password fields are write-only in serializers and never returned by APIs.
- Tokens are only returned by token endpoints.
- Audit records sanitize metadata and do not include passwords or token values.
- Imported CSV files are validated before persistence and bounded by a row limit.
- Synthetic-only mode requires registration, administrative creation and CSV imports to use usernames ending in `.invalid`.

## Audit logging

Audit middleware records authenticated POST, PUT, PATCH and DELETE requests outside health, static and token endpoints. Services also create explicit records for identity creation, role assignment, finding review, report generation and analysis execution.

## Safe analysis boundary

IdentityForge reads access configuration and event data, calculates risk paths and stores evidence. It never attempts to exploit an identity system, assume a role, obtain credentials or perform unauthorized privilege escalation.

## Hardening checklist

| Control | Setting or feature |
| --- | --- |
| HTTPS redirect | `SECURE_SSL_REDIRECT` |
| Secure cookies | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` |
| HSTS | `SECURE_HSTS_SECONDS` |
| Clickjacking | `X_FRAME_OPTIONS=DENY` |
| Content type | `SECURE_CONTENT_TYPE_NOSNIFF` |
| CORS | `CORS_ALLOWED_ORIGINS` |
| Rate limiting | `API_THROTTLE_ANON`, `API_THROTTLE_USER` |

## Limitation

This project is a decision-support workspace. It does not replace production IAM governance, qualified human review or formal compliance assessment.
