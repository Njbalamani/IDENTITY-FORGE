# REST API Reference

All endpoints except registration and token issuance require authentication. Session clients must include CSRF tokens for state-changing requests. API clients should send `Authorization: Bearer <access_token>`.

## Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/auth/register/` | Register a viewer account in a synthetic organization |
| POST | `/api/auth/token/` | Obtain access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh an access token |
| GET | `/api/auth/me/` | Current authenticated identity |

## Identity and access

| Method | Endpoint | Description |
| --- | --- | --- |
| GET, POST | `/api/users/` | List or create identities |
| GET, POST | `/api/organizations/` | List or create organizations |
| GET, POST | `/api/teams/` | Manage teams |
| GET, POST | `/api/profiles/` | Manage identity profiles |
| GET, POST | `/api/permissions/` | Manage permission catalog |
| GET, POST | `/api/roles/` | Manage roles, inheritance and conflicts |
| GET, POST | `/api/assignments/` | Manage role assignments |
| GET, POST | `/api/resources/` | Manage access resources |
| GET | `/api/events/` | Query access events |
| POST | `/api/events/import_events/` | Upload and validate an access-event CSV |
| GET, POST | `/api/reviews/` | Manage access reviews |
| POST | `/api/reviews/{id}/complete/` | Approve or reject a review |

## Analysis and evidence

| Method | Endpoint | Description |
| --- | --- | --- |
| GET, PATCH | `/api/findings/` | List or update risk findings |
| POST | `/api/findings/{id}/review/` | Record a human review decision |
| GET | `/api/findings/export/` | Download organization-scoped findings as CSV |
| GET | `/api/anomalies/` | List scored anomaly results |
| GET | `/api/assessments/` | List Zero Trust assessments |
| GET | `/api/analysis-runs/` | List analysis history |
| GET | `/api/graph/` | Graph nodes, links and summary |
| GET | `/api/dashboard/metrics/` | Live dashboard metrics and Zero Trust trend |
| POST | `/api/analysis/run/` | Trigger an analysis type |
| GET | `/api/ai/status/` | Model and disclaimer metadata |
| GET | `/api/reports/` | List generated PDF reports |
| POST | `/api/reports/generate/` | Generate a PDF report |
| GET | `/api/audit-logs/` | Query audit history |

## Access certification

| Method | Endpoint | Description |
| --- | --- | --- |
| GET, POST | `/api/certification-campaigns/` | List or create certification campaigns |
| POST | `/api/certification-campaigns/{id}/apply/` | Apply decisions and complete a campaign |
| POST | `/api/certification-campaigns/{id}/cancel/` | Cancel an active campaign |
| GET | `/api/certification-items/` | List campaign items |
| POST | `/api/certification-items/{id}/decide/` | Record APPROVED, REVOKED or EXCEPTION |

## Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health/live/` | Liveness probe |
| GET | `/health/ready/` | Database readiness probe |

## Authorization boundaries

- `ADMIN` can manage users, organizations and all analysis actions.
- `SECURITY_ANALYST` can manage access configuration and run analysis.
- `REVIEWER` can review findings and complete access reviews.
- `VIEWER` has read-only access to scoped records.
- All organization-scoped viewsets filter by the authenticated user's organization.
