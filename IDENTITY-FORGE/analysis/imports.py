from django.conf import settings
from django.contrib.auth import get_user_model

from access.models import AccessEvent, AccessResource

REQUIRED_COLUMNS = {"username", "event_type", "occurred_at", "success", "resource", "source"}
MAX_IMPORT_ROWS = 10000


def validate_access_event_csv(uploaded_file, organization=None):
    import pandas as pd

    try:
        frame = pd.read_csv(uploaded_file)
    except Exception as exc:
        raise ValueError(f"Unable to parse CSV: {exc}") from exc
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if len(frame) > MAX_IMPORT_ROWS:
        raise ValueError(f"Import exceeds the {MAX_IMPORT_ROWS}-row limit")
    if frame.empty:
        raise ValueError("Import contains no rows")

    user_query = get_user_model().objects.all()
    if organization:
        user_query = user_query.filter(organization=organization)
    users = set(user_query.values_list("username", flat=True))
    unknown = sorted(
        {value for value in frame["username"].dropna().astype(str) if value not in users}
    )
    if unknown:
        raise ValueError(f"Unknown usernames: {', '.join(unknown[:5])}")

    valid_events = set(AccessEvent.EventType.values)
    invalid_events = sorted(
        {value for value in frame["event_type"].dropna().astype(str) if value not in valid_events}
    )
    if invalid_events:
        raise ValueError(f"Unsupported event types: {', '.join(invalid_events[:5])}")

    parsed_time = pd.to_datetime(frame["occurred_at"], errors="coerce", utc=True)
    if parsed_time.isna().any():
        raise ValueError("One or more occurred_at values are not valid timestamps")

    if settings.SYNTHETIC_DATA_ONLY:
        synthetic_query = user_query.filter(username__endswith=".invalid")
        synthetic_users = set(synthetic_query.values_list("username", flat=True))
        if not synthetic_users.issuperset(set(frame["username"].astype(str))):
            raise ValueError("Synthetic-only mode requires usernames ending in .invalid")

    records = []
    for index, row in frame.iterrows():
        records.append(
            {
                "username": str(row["username"]),
                "event_type": str(row["event_type"]),
                "occurred_at": parsed_time.iloc[index].to_pydatetime(),
                "success": str(row["success"]).strip().lower() in {"1", "true", "yes", "y"},
                "resource": str(row.get("resource") or "").strip(),
                "source": AccessEvent.Source.IMPORTED,
                "ip_address": str(row.get("ip_address") or "").strip() or None,
                "user_agent": str(row.get("user_agent") or "")[:300],
                "metadata": {"imported_row": index + 1},
            }
        )
    return records


def import_access_events(organization, uploaded_file):
    records = validate_access_event_csv(uploaded_file, organization)
    users = {
        user.username: user for user in get_user_model().objects.filter(organization=organization)
    }
    resources = {
        resource.name: resource
        for resource in AccessResource.objects.filter(organization=organization)
    }
    events = []
    for record in records:
        user = users.get(record["username"])
        if not user:
            continue
        resource = resources.get(record["resource"]) if record["resource"] else None
        events.append(
            AccessEvent(
                organization=organization,
                user=user,
                event_type=record["event_type"],
                occurred_at=record["occurred_at"],
                success=record["success"],
                resource=resource,
                source=record["source"],
                ip_address=record["ip_address"],
                user_agent=record["user_agent"],
                metadata=record["metadata"],
            )
        )
    AccessEvent.objects.bulk_create(events)
    return len(events)
