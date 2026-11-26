from audit.models import AuditLog


def log_action(
    organization, actor, action, target_type="", target_id="", metadata=None, ip_address=None
):
    return AuditLog.objects.create(
        organization=organization,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id or ""),
        metadata=metadata or {},
        ip_address=ip_address,
    )
