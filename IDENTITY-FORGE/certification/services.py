from django.db import transaction
from django.utils import timezone

from access.models import RoleAssignment
from audit.services import log_action
from certification.models import Campaign, CampaignItem

DECIDED_STATUSES = {
    CampaignItem.Decision.APPROVED,
    CampaignItem.Decision.REVOKED,
    CampaignItem.Decision.EXCEPTION,
}


def populate_campaign(campaign):
    assignments = RoleAssignment.objects.filter(
        user__organization=campaign.organization, active=True
    ).select_related("user", "role")
    items = [
        CampaignItem(
            campaign=campaign,
            user=assignment.user,
            role=assignment.role,
            assignment=assignment,
        )
        for assignment in assignments
    ]
    CampaignItem.objects.bulk_create(items, ignore_conflicts=True)
    return len(items)


def create_campaign(organization, created_by, name, due_date, reviewers=(), ip_address=None):
    with transaction.atomic():
        campaign = Campaign.objects.create(
            organization=organization,
            name=name,
            due_date=due_date,
            created_by=created_by,
        )
        campaign.reviewers.set(reviewers)
        count = populate_campaign(campaign)
        log_action(
            organization,
            created_by,
            "Created certification campaign",
            "Campaign",
            campaign.id,
            {"name": name, "items": count},
            ip_address,
        )
    return campaign


def decide_item(item, actor, decision, note="", ip_address=None):
    if decision not in DECIDED_STATUSES:
        raise ValueError("decision must be APPROVED, REVOKED or EXCEPTION.")
    if item.campaign.status != Campaign.Status.ACTIVE:
        raise ValueError("Certification campaign is not active.")
    item.decision = decision
    item.note = note
    item.decided_by = actor
    item.decided_at = timezone.now()
    item.save(update_fields=["decision", "note", "decided_by", "decided_at"])
    log_action(
        item.campaign.organization,
        actor,
        "Recorded certification decision",
        "CampaignItem",
        item.id,
        {"campaign": item.campaign_id, "decision": decision, "username": item.user.username},
        ip_address,
    )
    return item


def apply_decisions(campaign, actor, ip_address=None):
    if campaign.status != Campaign.Status.ACTIVE:
        raise ValueError("Certification campaign is not active.")
    pending = campaign.items.filter(decision=CampaignItem.Decision.PENDING).count()
    if pending:
        raise ValueError(f"{pending} certification item(s) are still pending.")
    revoked_items = list(
        campaign.items.filter(
            decision=CampaignItem.Decision.REVOKED,
            assignment__isnull=False,
            assignment__active=True,
        ).select_related("assignment", "user", "role")
    )
    with transaction.atomic():
        revoked_count = 0
        for item in revoked_items:
            assignment = item.assignment
            assignment.active = False
            assignment.save(update_fields=["active"])
            log_action(
                campaign.organization,
                actor,
                "Revoked certified access",
                "RoleAssignment",
                assignment.id,
                {
                    "campaign": campaign.id,
                    "username": item.user.username,
                    "role": item.role.code,
                },
                ip_address,
            )
            revoked_count += 1
        campaign.status = Campaign.Status.COMPLETED
        campaign.completed_at = timezone.now()
        campaign.save(update_fields=["status", "completed_at"])
        log_action(
            campaign.organization,
            actor,
            "Applied certification decisions",
            "Campaign",
            campaign.id,
            {"revoked": revoked_count, "items": campaign.items.count()},
            ip_address,
        )
    return revoked_count


def cancel_campaign(campaign, actor, ip_address=None):
    if campaign.status != Campaign.Status.ACTIVE:
        raise ValueError("Certification campaign is not active.")
    campaign.status = Campaign.Status.CANCELLED
    campaign.completed_at = timezone.now()
    campaign.save(update_fields=["status", "completed_at"])
    log_action(
        campaign.organization,
        actor,
        "Cancelled certification campaign",
        "Campaign",
        campaign.id,
        {"name": campaign.name},
        ip_address,
    )
    return campaign
