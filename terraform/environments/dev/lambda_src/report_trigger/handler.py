"""
EventBridge-triggered report generator.

Only used when var.enable_external_scheduler = true. The app already runs its own
in-process APScheduler (see app/main.py) whenever the ECS task is up — this Lambda
is an *alternative*, decoupled trigger path: instead of duplicating the scheduling
logic here, it just calls the running app's own /api/reports/{period} endpoint over
HTTP. That way there's exactly one place (the FastAPI app) that knows how to build
a report; this function just knocks on the door at the scheduled time.

Uses only the standard library (urllib) so no extra packaging/layers are needed.
"""

import json
import os
import urllib.request

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")


def lambda_handler(event, context):
    period = (event or {}).get("period", "daily")
    if period not in ("daily", "weekly", "monthly"):
        raise ValueError(f"Invalid period: {period}")

    if not DASHBOARD_URL:
        raise RuntimeError("DASHBOARD_URL environment variable is not set")

    url = f"{DASHBOARD_URL}/api/reports/{period}"
    req = urllib.request.Request(url, method="POST")
    if API_KEY:
        req.add_header("X-API-Key", API_KEY)

    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read().decode("utf-8")
        status = resp.status

    print(f"report_trigger period={period} status={status} body={body[:500]}")
    return {"statusCode": status, "body": json.loads(body) if body else None}
