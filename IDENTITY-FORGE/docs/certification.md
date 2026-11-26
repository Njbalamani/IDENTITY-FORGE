# Access Certification Workflow

Certification campaigns snapshot active role assignments for an organization and route each identity/role pair through an accountable human decision. This is a governance workflow, not an automated privilege-granting engine.

## Lifecycle

1. A security analyst or administrator creates a campaign with a due date and reviewers.
2. The campaign copies every active `RoleAssignment` in the organization into a `CampaignItem`.
3. Assigned reviewers record `APPROVED`, `REVOKED` or `EXCEPTION`, with a note.
4. Applying decisions deactivates role assignments for `REVOKED` items and marks the campaign `COMPLETED`.
5. Campaigns with outstanding `PENDING` items cannot be applied.

## Safety properties

- Creation snapshots assignments; later access changes do not alter existing items.
- Review authorization is explicit through the campaign reviewer list or platform administrator role.
- Applying decisions only deactivates assignments that were explicitly revoked in the campaign.
- Every create, decision, revocation and apply action writes an audit log entry.
- Analysis engines do not create campaigns or apply decisions.

## Interfaces

- UI: `/certifications/`
- REST: `/api/certification-campaigns/`, `/api/certification-items/`
- Dashboard: active campaign and pending decision counters

Campaigns are synthetic when the source assignments are synthetic. Never populate this workflow with production access data.
