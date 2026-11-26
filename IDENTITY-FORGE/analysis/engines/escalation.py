from collections import deque

from access.models import Role


class EscalationEngine:
    def __init__(self, organization):
        self.organization = organization

    @staticmethod
    def find_high_risk_path(role):
        queue = deque([(role, [role])])
        seen = {role.id}
        while queue:
            current, path = queue.popleft()
            if current.permissions.filter(is_high_risk=True).exists() or current.is_privileged:
                return path
            for parent in current.inherits.all():
                if parent.id not in seen:
                    seen.add(parent.id)
                    queue.append((parent, path + [parent]))
        return []

    def analyze(self):
        findings = []
        roles = Role.objects.filter(organization=self.organization).prefetch_related(
            "inherits", "permissions"
        )
        for role in roles:
            path = self.find_high_risk_path(role)
            if len(path) < 2 or role.is_privileged:
                continue
            target = path[-1]
            permissions = list(
                target.permissions.filter(is_high_risk=True).values_list("code", flat=True)
            )
            findings.append(
                {
                    "title": f"Privilege inheritance path from {role.name}",
                    "description": f"{role.name} can inherit access associated with {target.name} without being marked privileged.",
                    "severity": "CRITICAL" if permissions else "HIGH",
                    "score": 90 if permissions else 75,
                    "evidence": {
                        "path": [item.name for item in path],
                        "role_ids": [item.id for item in path],
                        "high_risk_permissions": permissions,
                    },
                    "recommendation": "Remove the inheritance edge, mark the source role privileged deliberately, or require an access review.",
                    "category": "ESCALATION_PATH",
                }
            )
        return findings
