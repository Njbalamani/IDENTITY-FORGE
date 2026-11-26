import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder

from access.models import AccessEvent
from analysis.engines.anomaly import AnomalyEngine
from analysis.engines.graph import AccessGraphEngine
from organizations.models import Organization


class Command(BaseCommand):
    help = "Run IdentityForge deployment health checks"

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true")

    def handle(self, *args, **options):
        checks = []
        checks.append(self.database_check())
        checks.append(self.migration_check())
        checks.append(self.static_check())
        checks.append(self.sample_check())
        checks.append(self.engine_check())
        checks.append(self.synthetic_check())
        failed = [check for check in checks if not check["ok"]]
        payload = {
            "status": "ok" if not failed else "failed",
            "checks": checks,
        }
        if options["json"]:
            self.stdout.write(json.dumps(payload, indent=2))
        else:
            for check in checks:
                marker = "OK" if check["ok"] else "FAIL"
                self.stdout.write(f"[{marker}] {check['name']}: {check['detail']}")
        if failed:
            raise CommandError(
                f"IdentityForge health checks failed: {', '.join(item['name'] for item in failed)}"
            )

    @staticmethod
    def result(name, ok, detail):
        return {"name": name, "ok": ok, "detail": detail}

    def database_check(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return self.result("database", True, "database connection available")
        except Exception as exc:
            return self.result("database", False, str(exc))

    def migration_check(self):
        try:
            applied = set(MigrationRecorder(connection).applied_migrations())
            loader = MigrationLoader(connection, ignore_no_migrations=True)
            missing = sorted(set(loader.graph.nodes) - applied)
            return self.result(
                "migrations",
                not missing,
                "all migrations applied" if not missing else f"missing: {missing}",
            )
        except Exception as exc:
            return self.result("migrations", False, str(exc))

    def static_check(self):
        static_dir = settings.BASE_DIR / "static"
        ok = static_dir.is_dir() and (static_dir / "css" / "main.css").exists()
        return self.result(
            "static_assets", ok, "static assets present" if ok else "static assets missing"
        )

    def sample_check(self):
        directory = settings.BASE_DIR / "samples" / "data"
        required = [
            "users.csv",
            "roles.csv",
            "permissions.csv",
            "assignments.csv",
            "resources.csv",
            "access_events.csv",
        ]
        missing = [name for name in required if not (directory / name).exists()]
        return self.result(
            "synthetic_samples",
            not missing,
            "sample CSVs present" if not missing else f"missing: {missing}",
        )

    def engine_check(self):
        try:
            organization = Organization.objects.order_by("name").first()
            graph = (
                AccessGraphEngine(organization).to_payload()
                if organization
                else {"nodes": [], "links": [], "summary": {}}
            )
            events = list(AccessEvent.objects.all()[:500])
            anomalies = AnomalyEngine(organization).analyze(events) if organization else []
            detail = f"graph nodes={len(graph['nodes'])}, anomaly profiles={len(anomalies)}"
            return self.result("analysis_engines", True, detail)
        except Exception as exc:
            return self.result("analysis_engines", False, str(exc))

    def synthetic_check(self):
        directory = Path(settings.BASE_DIR) / "samples" / "data" / "users.csv"
        ok = settings.SYNTHETIC_DATA_ONLY and directory.exists()
        return self.result(
            "synthetic_only",
            ok,
            "synthetic-only mode enabled"
            if ok
            else "synthetic-only mode disabled or sample missing",
        )
