import json
import logging

import azure.functions as func

from src.pipeline.config import load_config
from src.pipeline.extraction import extract_record
from src.pipeline.http_client import fetch_page

bp = func.Blueprint()
logger = logging.getLogger(__name__)


@bp.route(route="extract-url", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_extract_url(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        url = body.get("url")
        if not url:
            return func.HttpResponse("Missing required field: url", status_code=400)

        page = fetch_page(url)
        record = extract_record(page.final_url, page.title, page.text, load_config())
        return func.HttpResponse(
            json.dumps({"record": record.model_dump(), "textLength": len(page.text)}),
            mimetype="application/json",
        )
    except Exception as exc:
        logger.exception("URL extraction failed: %s", exc)
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=500, mimetype="application/json")
