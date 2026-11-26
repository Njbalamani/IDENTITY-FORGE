# Risk Engine Logic

## Permission evaluation

The permission engine walks direct role assignments and role inheritance edges. Effective permissions are the union of permissions granted by all reachable roles.

Findings are generated for:

- High-risk permissions reachable through inheritance.
- High-risk permission counts above `HIGH_RISK_PERMISSION_LIMIT`.
- Mutually exclusive roles assigned together.
- Inactive identities that retain active assignments.
- Individually high-risk permissions with risk weight of at least 8.

## Access graph

The graph contains users, teams, roles, permissions and resources. Edge types include `ASSIGNED`, `MEMBER`, `TEAM_ROLE`, `INHERITS`, `GRANTS`, `REQUIRES` and `ACCESSED`. NetworkX shortest paths identify indirect resource access and privileged intermediate roles.

3D coordinates come from a seeded NetworkX spring layout so the Three.js view is stable across runs.

## Privilege escalation analysis

The escalation engine follows configured role inheritance edges. If a non-privileged role reaches a role with high-risk permissions, it records the path, the high-risk permission codes and a recommended fix. No actual access is exercised.

## Anomaly detection

Access events are grouped by user and date. Features are computed from observed events:

- Event count
- Failed authentication ratio
- Unique resource count
- Privileged action ratio
- Off-hours event count
- MFA challenge ratio

When at least `ANOMALY_MIN_SAMPLES` user-day profiles exist, Isolation Forest scores the feature matrix with a fixed random seed and configured contamination. Below that threshold, a statistical baseline uses standard deviations from the observed same dataset. Every flag includes the features that contributed to the score.

## Zero Trust scoring

Scores are weighted from `ZERO_TRUST_RULES`:

| Category | Evidence |
| --- | --- |
| Least privilege | Users with excessive permission findings |
| Authentication | MFA coverage from identity profiles |
| Role separation | Users with conflicting role findings |
| Session controls | Session timeout limits |
| Access reviews | Overdue review count |
| Account lifecycle | Inactive identities with active access |

Scores and recommendations are stored as assessment snapshots and included in PDF reports.

## Control mapping

Each finding category maps to NIST CSF 2.0 references, CIS Controls v8 practices and Zero Trust principles. These mappings are advisory labels for triage and reporting; they are exposed through the REST API, findings table, CSV export and generated PDFs. They do not replace a formal control assessment.
