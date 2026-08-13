from unittest.mock import patch

from app.alerts.notifier import notify_anomaly, notify_cost_summary, send_email, send_slack_message


@patch("app.alerts.notifier.get_settings")
@patch("app.alerts.notifier.WebhookClient")
def test_send_slack_message_success(mock_webhook, mock_settings):
    mock_settings.return_value.slack_webhook_url = "https://hooks.slack.com/services/test"
    mock_webhook.return_value.send.return_value.status_code = 200

    result = send_slack_message("Test message")
    assert result is True


@patch("app.alerts.notifier.get_settings")
@patch("app.alerts.notifier.get_ses_client")
def test_send_email_success(mock_ses, mock_settings):
    mock_settings.return_value.ses_from_email = "sender@example.com"
    mock_settings.return_value.ses_to_emails = ["receiver@example.com"]
    mock_ses.return_value.send_email.return_value = {"MessageId": "12345"}

    result = send_email("Subject", "<p>Body</p>")
    assert result is True


@patch("app.alerts.notifier.send_slack_message")
@patch("app.alerts.notifier.send_email")
def test_notify_cost_summary(mock_send_email, mock_send_slack):
    summary = {
        "current_total": 1500.50,
        "previous_total": 1200.00,
        "change_pct": 25.0,
        "start": "2026-08-01",
        "end": "2026-08-12",
        "top_services": [{"service": "Amazon EC2", "amount": 800.00}],
    }
    notify_cost_summary(summary)
    assert mock_send_slack.called
    assert mock_send_email.called


@patch("app.alerts.notifier.send_slack_message")
@patch("app.alerts.notifier.send_email")
def test_notify_anomaly(mock_send_email, mock_send_slack):
    anomaly = {
        "Impact": {"TotalImpact": 250.0},
        "AnomalyStartDate": "2026-08-10",
        "AnomalyScore": {"CurrentScore": 0.95},
    }
    notify_anomaly(anomaly)
    assert mock_send_slack.called
    assert mock_send_email.called
