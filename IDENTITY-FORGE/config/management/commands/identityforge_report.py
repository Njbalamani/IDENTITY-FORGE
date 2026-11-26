from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from organizations.models import Organization
from reports.models import Report
from reports.services import generate_report


class Command(BaseCommand):
    help = "Generate an IdentityForge PDF assessment report."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True, help="Organization slug or id")
        parser.add_argument(
            "--type",
            default=Report.ReportType.EXECUTIVE,
            choices=Report.ReportType.values,
        )
        parser.add_argument("--username", help="Optional username to record as report author")

    def handle(self, *args, **options):
        identifier = options["organization"]
        organization = Organization.objects.filter(slug=identifier).first()
        if not organization and identifier.isdigit():
            organization = Organization.objects.filter(id=int(identifier)).first()
        if not organization:
            raise CommandError(f"Organization not found: {identifier}")

        actor = None
        username = options.get("username")
        if username:
            actor = (
                get_user_model()
                .objects.filter(username=username, organization=organization)
                .first()
            )
            if not actor:
                raise CommandError(f"User not found in organization: {username}")

        report = generate_report(organization, options["type"], actor)
        if options.get("verbosity", 1) > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Generated report {report.id}: {report.file.name}")
            )
