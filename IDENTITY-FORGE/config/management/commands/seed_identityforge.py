from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from access.models import (
    AccessEvent,
    AccessResource,
    AccessReview,
    Permission,
    Role,
    RoleAssignment,
)
from accounts.models import User
from analysis.services import run_all_analyses
from certification.models import Campaign
from certification.services import create_campaign
from identities.models import IdentityProfile, Team
from organizations.models import Organization
from samples.generate_synthetic_dataset import generate_dataset


class Command(BaseCommand):
    help = "Seed IdentityForge with deterministic synthetic identity and access data"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--skip-analysis", action="store_true")

    def handle(self, *args, **options):
        data = generate_dataset(options["seed"])
        organization, _ = Organization.objects.update_or_create(
            slug="northstar-health",
            defaults={
                "name": "Northstar Health",
                "description": "Synthetic identity security demonstration workspace",
                "industry": "Healthcare",
                "synthetic": True,
            },
        )

        teams = {}
        for item in data["teams"]:
            teams[item["slug"]], _ = Team.objects.update_or_create(
                organization=organization,
                name=item["name"],
                defaults={"description": item["description"]},
            )
        for item in data["teams"]:
            if item["parent"]:
                team = teams[item["slug"]]
                team.parent = teams[item["parent"]]
                team.save(update_fields=["parent"])

        permissions = {}
        for item in data["permissions"]:
            permissions[item["code"]], _ = Permission.objects.update_or_create(
                organization=organization,
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "category": item["category"],
                    "description": item["description"],
                    "risk_weight": item["risk_weight"],
                    "is_high_risk": item["is_high_risk"],
                },
            )

        roles = {}
        for item in data["roles"]:
            role, _ = Role.objects.update_or_create(
                organization=organization,
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "is_privileged": item["is_privileged"],
                    "risk_weight": item["risk_weight"],
                },
            )
            role.permissions.set([permissions[code] for code in item["permissions"]])
            roles[item["code"]] = role
        for item in data["roles"]:
            role = roles[item["code"]]
            role.inherits.set([roles[code] for code in item["inherits"]])
            role.conflicts.set([roles[code] for code in item["conflicts"]])

        user_model = get_user_model()
        users = {}
        for item in data["users"]:
            user, _ = user_model.objects.update_or_create(
                username=item["username"],
                defaults={
                    "email": item["email"],
                    "display_name": item["display_name"],
                    "platform_role": item["platform_role"],
                    "organization": organization,
                    "is_active": True,
                },
            )
            user.set_password("SyntheticPass!123")
            user.save(update_fields=["password"])
            users[item["username"]] = user
            IdentityProfile.objects.update_or_create(
                user=user,
                defaults={
                    "organization": organization,
                    "team": teams.get(item["team"]),
                    "employee_id": item["employee_id"],
                    "department": item["department"],
                    "title": item["title"],
                    "status": item["status"],
                    "mfa_enabled": item["mfa_enabled"],
                    "session_timeout_minutes": item["session_timeout_minutes"],
                    "last_activity_at": timezone.now(),
                    "risk_score": 0,
                },
            )

        for item in data["assignments"]:
            RoleAssignment.objects.update_or_create(
                user=users[item["username"]],
                role=roles[item["role_code"]],
                team=teams.get(item["team"]),
                defaults={
                    "source": item["source"],
                    "active": item["active"] == "TRUE",
                    "justification": item["justification"],
                },
            )

        for item in data["resources"]:
            resource, _ = AccessResource.objects.update_or_create(
                organization=organization,
                name=item["name"],
                defaults={
                    "resource_type": item["resource_type"],
                    "sensitivity": item["sensitivity"],
                    "description": item["description"],
                },
            )
            resource.permissions.set(
                [permissions[code] for code in item["permissions"].split(";") if code]
            )

        AccessEvent.objects.filter(
            organization=organization, source=AccessEvent.Source.SYNTHETIC
        ).delete()
        AccessEvent.objects.bulk_create(
            [
                AccessEvent(
                    organization=organization,
                    user=users[item["username"]],
                    event_type=item["event_type"],
                    occurred_at=datetime.fromisoformat(item["occurred_at"]),
                    success=item["success"] == "TRUE",
                    resource=AccessResource.objects.get(
                        organization=organization, name=item["resource"]
                    ),
                    ip_address=item["ip_address"],
                    user_agent=item["user_agent"],
                    source=AccessEvent.Source.SYNTHETIC,
                    metadata={},
                )
                for item in data["events"]
            ]
        )

        AccessReview.objects.filter(organization=organization).delete()
        AccessReview.objects.bulk_create(
            [
                AccessReview(
                    organization=organization,
                    user=users[item["username"]],
                    status=AccessReview.Status.PENDING,
                    due_date=datetime.fromisoformat(item["due_date"]),
                    notes=item["notes"],
                )
                for item in data["reviews"]
            ]
        )

        Campaign.objects.filter(
            organization=organization, name="Quarterly access certification"
        ).delete()
        campaign_owner = user_model.objects.filter(
            organization=organization, platform_role=User.PlatformRole.ADMIN
        ).first() or next(iter(users.values()))
        certification_reviewers = user_model.objects.filter(
            organization=organization,
            platform_role__in=[
                User.PlatformRole.ADMIN,
                User.PlatformRole.SECURITY_ANALYST,
                User.PlatformRole.REVIEWER,
            ],
            is_active=True,
        )
        campaign = create_campaign(
            organization,
            campaign_owner,
            "Quarterly access certification",
            timezone.now().date() + timedelta(days=30),
            certification_reviewers,
        )

        result = {}
        if not options["skip_analysis"]:
            result = run_all_analyses(organization)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(users)} identities, {len(roles)} roles, {len(data['events'])} events, "
                f"{campaign.items.count()} certification items. Analysis: {result}"
            )
        )
