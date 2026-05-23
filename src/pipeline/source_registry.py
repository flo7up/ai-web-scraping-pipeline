from datetime import datetime, timedelta, timezone

from . import cosmos


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def upsert_source_page(url: str, revisit_frequency_days: int) -> dict:
    now = datetime.now(timezone.utc)
    item = {
        "id": url,
        "pk": "SourcePage#default",
        "url": url,
        "active": True,
        "lastVisitedAt": None,
        "nextVisitAfter": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "revisitFrequencyDays": revisit_frequency_days,
    }
    return cosmos.upsert("source_pages", item)


def mark_source_visited(url: str, revisit_frequency_days: int) -> dict:
    now = datetime.now(timezone.utc)
    next_visit = now + timedelta(days=revisit_frequency_days)
    item = {
        "id": url,
        "pk": "SourcePage#default",
        "url": url,
        "active": True,
        "lastVisitedAt": utc_now_iso(),
        "nextVisitAfter": next_visit.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "revisitFrequencyDays": revisit_frequency_days,
    }
    return cosmos.upsert("source_pages", item)


def due_source_pages(limit: int = 25) -> list[dict]:
    now = utc_now_iso()
    return cosmos.query(
        "source_pages",
        "SELECT TOP @limit * FROM c WHERE c.pk = @pk AND c.active = true AND c.nextVisitAfter <= @now",
        parameters=[
            {"name": "@limit", "value": limit},
            {"name": "@pk", "value": "SourcePage#default"},
            {"name": "@now", "value": now},
        ],
        enable_cross_partition_query=False,
        partition_key="SourcePage#default",
    )
