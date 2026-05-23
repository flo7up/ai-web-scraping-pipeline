from . import cosmos
from .models import utc_now_iso


def log_run(name: str, status: str, detail: dict | None = None) -> dict:
    item = {
        "id": f"{name}:{utc_now_iso()}",
        "PartitionKey": "pipeline-run",
        "name": name,
        "status": status,
        "detail": detail or {},
        "timestamp": utc_now_iso(),
    }
    return cosmos.upsert("runs", item)
