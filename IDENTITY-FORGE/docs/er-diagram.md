# Entity Relationship Diagram

```mermaid
erDiagram
    Organization ||--o{ User : has_members
    Organization ||--o{ Team : owns
    Organization ||--o{ IdentityProfile : scopes
    Organization ||--o{ Permission : defines
    Organization ||--o{ Role : defines
    Organization ||--o{ AccessResource : owns
    Organization ||--o{ AccessEvent : records
    Organization ||--o{ RiskFinding : tracks
    Organization ||--o{ AnomalyResult : tracks
    Organization ||--o{ ZeroTrustAssessment : evaluates
    Organization ||--o{ AccessReview : schedules
    Organization ||--o{ Report : stores
    Organization ||--o{ AuditLog : logs

    Team ||--o{ IdentityProfile : contains
    User ||--o| IdentityProfile : described_by
    User ||--o{ RoleAssignment : receives
    Role ||--o{ RoleAssignment : granted_through
    Role ||--o{ Role : inherits
    Role ||--o{ Permission : grants
    AccessResource ||--o{ Permission : requires
    User ||--o{ AccessEvent : generates
    AccessResource ||--o{ AccessEvent : referenced_by
    User ||--o{ AnomalyResult : scored_by
    User ||--o{ RiskFinding : associated_with
    AuditLog ||--o| User : actor
```

## Model summary

| Model | Core fields | Purpose |
| --- | --- | --- |
| `User` | `username`, `platform_role`, `organization` | Authentication and RBAC |
| `Organization` | `name`, `slug`, `synthetic` | Workspace boundary |
| `Team` | `organization`, `parent` | Organizational hierarchy |
| `IdentityProfile` | `status`, `mfa_enabled`, `session_timeout_minutes` | Account posture |
| `Permission` | `code`, `risk_weight`, `is_high_risk` | Risk-weighted capability |
| `Role` | `inherits`, `conflicts`, `is_privileged` | Permission bundle and relationships |
| `RoleAssignment` | `user`, `role`, `team`, `active` | Effective access source |
| `AccessResource` | `sensitivity`, `permissions` | Protected asset |
| `AccessEvent` | `event_type`, `occurred_at`, `success` | Behavioral evidence |
| `RiskFinding` | `category`, `severity`, `evidence`, `status` | Reviewable risk evidence |
| `AnomalyResult` | `anomaly_score`, `reasons`, `features` | Explainable outlier result |
| `ZeroTrustAssessment` | `score`, `category_scores`, `recommendations` | Control posture snapshot |
| `Report` | `report_type`, `file`, `summary` | Generated PDF evidence |
| `AuditLog` | `actor`, `action`, `metadata` | Administrative trail |
