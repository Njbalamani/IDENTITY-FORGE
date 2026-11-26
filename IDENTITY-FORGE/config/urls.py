from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_live(request):
    return JsonResponse({"status": "ok", "service": "IdentityForge"})


def health_ready(request):
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ready", "database": "ok"})
    except Exception as exc:
        return JsonResponse({"status": "unready", "database": str(exc)}, status=503)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", health_live, name="health-live"),
    path("health/ready/", health_ready, name="health-ready"),
    path("api/", include("config.api")),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("identities/", include("identities.urls")),
    path("access/", include("access.urls")),
    path("analysis/", include("analysis.urls")),
    path("reports/", include("reports.urls")),
    path("audit/", include("audit.urls")),
    path("certifications/", include("certification.urls")),
]
