import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_TIME = datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc)
ORGANIZATION_SLUG = "northstar-health"

PERMISSION_DATA = [
    ("IDENTITY_READ", "Read identity records", "IDENTITY", 1, False),
    ("IDENTITY_WRITE", "Modify identity records", "IDENTITY", 5, False),
    ("ROLE_ASSIGN", "Assign roles", "IDENTITY", 8, True),
    ("MFA_RESET", "Reset MFA factors", "IDENTITY", 7, False),
    ("DATA_READ", "Read internal datasets", "DATA", 2, False),
    ("DATA_EXPORT", "Export datasets", "DATA", 9, True),
    ("DATA_DELETE", "Delete datasets", "DATA", 10, True),
    ("ADMIN_CONSOLE", "Access administrative console", "ADMIN", 9, True),
    ("AUDIT_READ", "Read audit records", "ADMIN", 4, False),
    ("POLICY_EDIT", "Edit security policies", "ADMIN", 8, True),
    ("FINANCE_APPROVE", "Approve transactions", "FINANCE", 10, True),
    ("FINANCE_VIEW", "View financial records", "FINANCE", 4, False),
    ("CLOUD_DEPLOY", "Deploy cloud workloads", "OPERATIONS", 9, True),
    ("CLOUD_VIEW", "View cloud inventory", "OPERATIONS", 2, False),
    ("ENDPOINT_CONTROL", "Control endpoint agents", "OPERATIONS", 7, False),
    ("REPORT_GENERATE", "Generate risk reports", "ADMIN", 3, False),
    ("TOKEN_MANAGE", "Manage API tokens", "IDENTITY", 8, True),
    ("REVIEW_SIGN_OFF", "Sign off access reviews", "ADMIN", 6, False),
]

ROLE_DATA = [
    (
        "viewer",
        "Viewer",
        "Read-only access to synthetic records",
        False,
        1,
        ["IDENTITY_READ", "DATA_READ"],
        [],
        [],
    ),
    (
        "analyst",
        "Security Analyst",
        "Investigates identity risk findings",
        False,
        2,
        ["AUDIT_READ", "REPORT_GENERATE", "CLOUD_VIEW"],
        ["viewer"],
        [],
    ),
    (
        "engineer",
        "Platform Engineer",
        "Maintains cloud and endpoint systems",
        False,
        3,
        ["CLOUD_VIEW", "ENDPOINT_CONTROL"],
        ["viewer"],
        [],
    ),
    (
        "cloud_operator",
        "Cloud Operator",
        "Deploys cloud workloads",
        True,
        8,
        ["CLOUD_DEPLOY"],
        ["engineer"],
        [],
    ),
    (
        "reviewer",
        "Access Reviewer",
        "Approves access review evidence",
        False,
        4,
        ["REVIEW_SIGN_OFF", "AUDIT_READ"],
        ["analyst"],
        [],
    ),
    (
        "finance_approver",
        "Finance Approver",
        "Approves financial transactions",
        True,
        9,
        ["FINANCE_APPROVE", "FINANCE_VIEW"],
        [],
        ["admin"],
    ),
    (
        "incident_responder",
        "Incident Responder",
        "Responds to identity incidents",
        True,
        7,
        ["MFA_RESET", "TOKEN_MANAGE", "AUDIT_READ"],
        ["analyst"],
        [],
    ),
    (
        "auditor",
        "Auditor",
        "Independent assurance role",
        False,
        3,
        ["AUDIT_READ", "REPORT_GENERATE"],
        [],
        ["admin"],
    ),
    (
        "admin",
        "Administrator",
        "Full administrative access",
        True,
        10,
        ["ADMIN_CONSOLE", "POLICY_EDIT", "ROLE_ASSIGN", "DATA_DELETE", "DATA_EXPORT"],
        ["cloud_operator"],
        ["finance_approver", "auditor"],
    ),
]

TEAM_DATA = [
    ("security-operations", "Security Operations", None),
    ("cloud-platform", "Cloud Platform", None),
    ("finance", "Finance", None),
    ("clinical-systems", "Clinical Systems", None),
    ("internal-audit", "Internal Audit", None),
]

RESOURCE_DATA = [
    ("identity-console", "APPLICATION", "CONFIDENTIAL", ["IDENTITY_READ", "IDENTITY_WRITE"]),
    ("claims-warehouse", "DATABASE", "RESTRICTED", ["DATA_READ", "DATA_EXPORT"]),
    ("payment-ledger", "FINANCIAL", "RESTRICTED", ["FINANCE_VIEW", "FINANCE_APPROVE"]),
    ("cloud-control-plane", "CLOUD", "RESTRICTED", ["CLOUD_VIEW", "CLOUD_DEPLOY"]),
    ("endpoint-fleet", "ENDPOINT", "CONFIDENTIAL", ["ENDPOINT_CONTROL"]),
    ("audit-archive", "FILE_SYSTEM", "CONFIDENTIAL", ["AUDIT_READ"]),
    ("policy-engine", "APPLICATION", "RESTRICTED", ["POLICY_EDIT"]),
    ("reporting-portal", "APPLICATION", "INTERNAL", ["REPORT_GENERATE"]),
    ("token-service", "APPLICATION", "RESTRICTED", ["TOKEN_MANAGE"]),
    ("scheduler-api", "APPLICATION", "INTERNAL", ["IDENTITY_READ"]),
    ("research-vault", "DATABASE", "RESTRICTED", ["DATA_READ", "DATA_DELETE"]),
    ("public-site", "APPLICATION", "PUBLIC", []),
]

EVENT_TYPES = [
    "LOGIN",
    "LOGIN_FAILED",
    "LOGOUT",
    "RESOURCE_ACCESS",
    "MFA_CHALLENGE",
    "PERMISSION_CHANGE",
    "ROLE_ASSIGNED",
    "ADMIN_ACTION",
]


def generate_dataset(seed=42):
    random.seed(seed)
    permissions = [
        {
            "code": code,
            "name": name,
            "category": category,
            "risk_weight": weight,
            "is_high_risk": high_risk,
            "description": f"Synthetic permission for {name.lower()}",
        }
        for code, name, category, weight, high_risk in PERMISSION_DATA
    ]
    roles = [
        {
            "code": code,
            "name": name,
            "description": description,
            "is_privileged": privileged,
            "risk_weight": weight,
            "permissions": permission_codes,
            "inherits": inherits,
            "conflicts": conflicts,
        }
        for code, name, description, privileged, weight, permission_codes, inherits, conflicts in ROLE_DATA
    ]
    teams = [
        {"slug": slug, "name": name, "parent": parent, "description": f"Synthetic {name} team"}
        for slug, name, parent in TEAM_DATA
    ]

    first_names = [
        "aisha",
        "bryan",
        "chen",
        "dana",
        "elena",
        "farid",
        "grace",
        "hugo",
        "imani",
        "jonas",
        "kavya",
        "liam",
    ]
    last_names = [
        "chen",
        "patel",
        "okafor",
        "garcia",
        "novak",
        "rahman",
        "kim",
        "silva",
        "haddad",
        "murphy",
        "rao",
        "weber",
    ]
    platform_roles = [
        "VIEWER",
        "SECURITY_ANALYST",
        "REVIEWER",
        "SECURITY_ANALYST",
        "VIEWER",
        "ADMIN",
    ]
    team_slugs = [item["slug"] for item in teams]
    users = []
    for index in range(24):
        first = first_names[index % len(first_names)]
        last = last_names[(index * 5) % len(last_names)]
        username = f"{first}.{last}{index + 1}@example.invalid"
        status = "INACTIVE" if index in {17, 21} else "ACTIVE"
        users.append(
            {
                "username": username,
                "email": username,
                "display_name": f"{first.title()} {last.title()}",
                "platform_role": platform_roles[index % len(platform_roles)],
                "organization_slug": ORGANIZATION_SLUG,
                "status": status,
                "team": team_slugs[index % len(team_slugs)],
                "mfa_enabled": index % 7 != 5,
                "session_timeout_minutes": 90 if index in {3, 11, 18} else 30,
                "employee_id": f"IF-{1000 + index}",
                "department": teams[index % len(teams)]["name"],
                "title": "Synthetic Role",
            }
        )

    assignments = []
    for index, user in enumerate(users):
        base_role = [
            "viewer",
            "analyst",
            "engineer",
            "reviewer",
            "cloud_operator",
            "finance_approver",
        ][index % 6]
        assignments.append(
            {
                "username": user["username"],
                "role_code": base_role,
                "team": user["team"],
                "source": "DIRECT",
                "active": "TRUE",
                "justification": "Synthetic baseline assignment",
            }
        )
    assignments.extend(
        [
            {
                "username": users[0]["username"],
                "role_code": "admin",
                "team": "security-operations",
                "source": "DIRECT",
                "active": "TRUE",
                "justification": "Synthetic emergency elevation",
            },
            {
                "username": users[4]["username"],
                "role_code": "auditor",
                "team": "internal-audit",
                "source": "DIRECT",
                "active": "TRUE",
                "justification": "Synthetic assurance access",
            },
            {
                "username": users[6]["username"],
                "role_code": "admin",
                "team": "cloud-platform",
                "source": "TEAM",
                "active": "TRUE",
                "justification": "Synthetic conflicting assignment",
            },
            {
                "username": users[9]["username"],
                "role_code": "finance_approver",
                "team": "finance",
                "source": "DIRECT",
                "active": "TRUE",
                "justification": "Synthetic conflicting assignment",
            },
            {
                "username": users[13]["username"],
                "role_code": "incident_responder",
                "team": "security-operations",
                "source": "DIRECT",
                "active": "TRUE",
                "justification": "Synthetic incident access",
            },
            {
                "username": users[17]["username"],
                "role_code": "cloud_operator",
                "team": "cloud-platform",
                "source": "DIRECT",
                "active": "TRUE",
                "justification": "Stale assignment for inactive identity",
            },
        ]
    )

    resources = [
        {
            "name": name,
            "resource_type": resource_type,
            "sensitivity": sensitivity,
            "permissions": ";".join(permission_codes),
            "description": "Synthetic resource for assessment demonstrations",
        }
        for name, resource_type, sensitivity, permission_codes in RESOURCE_DATA
    ]

    events = []
    for index in range(360):
        user = users[index % len(users)]
        resource = resources[random.randrange(len(resources))]
        event_type = random.choice(EVENT_TYPES)
        anomaly_user = index % 47 == 0
        off_hour = anomaly_user or random.random() < 0.12
        hour = random.choice([2, 3, 4, 22]) if off_hour else random.randrange(7, 19)
        occurred = BASE_TIME - timedelta(
            days=random.randrange(0, 45),
            hours=random.randrange(0, 20),
            minutes=random.randrange(0, 60),
        )
        occurred = occurred.replace(hour=hour)
        events.append(
            {
                "username": user["username"],
                "event_type": "LOGIN_FAILED" if anomaly_user and index % 2 == 0 else event_type,
                "occurred_at": occurred.isoformat(),
                "success": "FALSE" if anomaly_user and index % 3 == 0 else "TRUE",
                "resource": resource["name"],
                "source": "SYNTHETIC",
                "ip_address": f"203.0.113.{random.randrange(1, 254)}",
                "user_agent": "IdentityForge-Synthetic-Agent/1.0",
                "metadata": "{}",
            }
        )

    reviews = []
    for index, user in enumerate(users[::3]):
        reviews.append(
            {
                "username": user["username"],
                "status": "OVERDUE" if index % 3 == 0 else "PENDING",
                "due_date": (BASE_TIME - timedelta(days=index)).isoformat(),
                "notes": "Synthetic access review",
            }
        )

    return {
        "permissions": permissions,
        "roles": roles,
        "teams": teams,
        "users": users,
        "assignments": assignments,
        "resources": resources,
        "events": events,
        "reviews": reviews,
    }


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_dataset(output_dir=None, seed=42):
    directory = Path(output_dir) if output_dir else Path(__file__).resolve().parent / "data"
    directory.mkdir(parents=True, exist_ok=True)
    data = generate_dataset(seed)
    write_csv(directory / "users.csv", data["users"], list(data["users"][0]))
    write_csv(directory / "permissions.csv", data["permissions"], list(data["permissions"][0]))
    write_csv(directory / "roles.csv", data["roles"], list(data["roles"][0]))
    write_csv(directory / "teams.csv", data["teams"], list(data["teams"][0]))
    write_csv(directory / "assignments.csv", data["assignments"], list(data["assignments"][0]))
    write_csv(directory / "resources.csv", data["resources"], list(data["resources"][0]))
    write_csv(directory / "access_events.csv", data["events"], list(data["events"][0]))
    write_csv(directory / "access_reviews.csv", data["reviews"], list(data["reviews"][0]))
    return directory
