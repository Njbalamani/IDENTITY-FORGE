from django.core.management.base import BaseCommand

from samples.generate_synthetic_dataset import write_dataset


class Command(BaseCommand):
    help = "Generate deterministic synthetic identity CSV files"

    def add_arguments(self, parser):
        parser.add_argument("--output", default=None)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **options):
        directory = write_dataset(options["output"], options["seed"])
        self.stdout.write(self.style.SUCCESS(f"Synthetic dataset written to {directory}"))
