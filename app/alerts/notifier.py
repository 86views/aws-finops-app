"""Slack + SES notification helpers."""

from __future__ import annotations

from typing import Any

import structlog
from slack_sdk.webhook import WebhookClient

from app.core.aws import get_ses_client
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


def send_slack_message(text: str, blocks: list[dict[str, Any]] | None = None) -> bool:
    settings = get_settings()
    if not settings.slack_webhook_url:
        logger.warning("slack_webhook_not_configured")
        return False

    client = WebhookClient(settings.slack_webhook_url)
    response = client.send(
        text=text,
        blocks=blocks,
    )
    ok = response.status_code == 200
    if not ok:
        logger.error("slack_send_failed", status=response.status_code, body=response.body)
    else:
        logger.info("slack_message_sent")
    return ok


def send_email(subject: str, body_html: str, body_text: str | None = None) -> bool:
    settings = get_settings()
    if not settings.ses_from_email or not settings.ses_to_emails:
        logger.warning("ses_not_configured")
        return False

    ses = get_ses_client()
    try:
        ses.send_email(
            Source=settings.ses_from_email,
            Destination={"ToAddresses": settings.ses_to_emails},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                    "Text": {"Data": body_text or subject, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("email_sent", to=settings.ses_to_emails)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("email_send_failed", error=str(exc))
        return False


def notify_cost_summary(summary: dict[str, Any], period: str = "daily") -> None:
    """Send a cost summary to Slack (and optionally email)."""
    change = summary.get("change_pct", 0)
    emoji = "📈" if change > 5 else "📉" if change < -5 else "➡️"
    text = (
        f"{emoji} *AWS FinOps {period.capitalize()} Summary*\n"
        f"• Total: `${summary.get('current_total', 0):,.2f}`\n"
        f"• Change: `{change:+.1f}%` vs previous period\n"
        f"• Period: {summary.get('start')} → {summary.get('end')}"
    )

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"AWS FinOps {period.capitalize()} Report"},
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Current Total*\n`${summary.get('current_total', 0):,.2f}`",
                },
                {"type": "mrkdwn", "text": f"*Change*\n`{change:+.1f}%`"},
                {
                    "type": "mrkdwn",
                    "text": f"*Previous*\n`${summary.get('previous_total', 0):,.2f}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Period*\n{summary.get('start')} → {summary.get('end')}",
                },
            ],
        },
    ]

    top = summary.get("top_services", [])[:5]
    if top:
        lines = "\n".join(f"• {s['service']}: `${s['amount']:,.2f}`" for s in top)
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Top Services*\n{lines}"}}
        )

    send_slack_message(text, blocks=blocks)

    # lightweight HTML email
    html = f"""
    <h2>AWS FinOps {period.capitalize()} Report</h2>
    <p><strong>Total:</strong> ${summary.get("current_total", 0):,.2f}<br>
       <strong>Change:</strong> {change:+.1f}%<br>
       <strong>Period:</strong> {summary.get("start")} → {summary.get("end")}</p>
    <h3>Top Services</h3>
    <ul>
    {"".join(f"<li>{s['service']}: ${s['amount']:,.2f}</li>" for s in top)}
    </ul>
    """
    send_email(
        subject=f"[FinOps] {period.capitalize()} cost report – ${summary.get('current_total', 0):,.2f}",
        body_html=html,
    )


def notify_anomaly(anomaly: dict[str, Any]) -> None:
    """Notify about a detected cost anomaly."""
    impact = anomaly.get("Impact", {}).get("TotalImpact", 0)
    text = (
        f"🚨 *AWS Cost Anomaly Detected*\n"
        f"• Impact: `${float(impact):,.2f}`\n"
        f"• Start: {anomaly.get('AnomalyStartDate', 'N/A')}\n"
        f"• Score: {anomaly.get('AnomalyScore', {}).get('CurrentScore', 'N/A')}"
    )
    send_slack_message(text)
    send_email(
        subject=f"[FinOps] Cost anomaly – impact ${float(impact):,.2f}",
        body_html=f"<p>{text.replace(chr(10), '<br>')}</p>",
    )
