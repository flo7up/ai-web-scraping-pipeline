import json

import azure.functions as func

from src.pipeline import cosmos

bp = func.Blueprint()


@bp.route(route="records", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def http_search_records(req: func.HttpRequest) -> func.HttpResponse:
    query = (req.params.get("q") or "").strip()
    limit = min(int(req.params.get("limit") or 25), 100)

    if query:
        sql = "SELECT TOP @limit * FROM c WHERE c.PartitionKey = @pk AND (CONTAINS(c.title, @q, true) OR CONTAINS(c.summary, @q, true))"
        params = [
            {"name": "@limit", "value": limit},
            {"name": "@pk", "value": "record"},
            {"name": "@q", "value": query},
        ]
    else:
        sql = "SELECT TOP @limit * FROM c WHERE c.PartitionKey = @pk"
        params = [{"name": "@limit", "value": limit}, {"name": "@pk", "value": "record"}]

    items = cosmos.query("records", sql, parameters=params, enable_cross_partition_query=False, partition_key="record")
    return func.HttpResponse(json.dumps({"items": items, "count": len(items)}), mimetype="application/json")
