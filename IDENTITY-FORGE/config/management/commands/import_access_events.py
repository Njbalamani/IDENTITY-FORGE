from django.core.management.base import BaseCommand

from analysis.imports import import_access_events
from analysis.services import run_anomaly_analysis
from organizations.models import Organization


class Command(BaseCommand):
    help = "Validate and import an access-event CSV into an organization"

    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument("--organization", required=True)

    def handle(self, *args, **options):
        organization = Organization.objects.filter(slug=options["organization"]).first()
        if not organization:
            organization = Organization.objects.filter(id=options["organization"]).first()
        if not organization:
            self.stderr.write("Organization not found")
            return
        with open(options["file"], "rb") as handle:
            count = import_access_events(organization, handle)
        result = run_anomaly_analysis(organization)
        self.stdout.write(self.style.SUCCESS(f"Imported {count} events. Anomaly result: {result}"))
