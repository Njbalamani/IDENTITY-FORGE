from audit.models import AuditLog


class AuditMiddleware:
    EXEMPT_PREFIXES = ("/api/token/", "/health/", "/static/", "/media/", "/admin/login/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.record(request, response)
        return response

    def record(self, request, response):
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return
        if any(request.path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return
        try:
            AuditLog.objects.create(
                organization=getattr(user, "organization", None),
                actor=user,
                action=f"{request.method} {request.path}",
                target_type="HTTP_REQUEST",
                target_id="",
                metadata={"status_code": response.status_code, "path": request.path},
                ip_address=self.client_ip(request),
            )
        except Exception:
            return

    @staticmethod
    def client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
