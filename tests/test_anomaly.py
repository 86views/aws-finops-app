from unittest.mock import patch

from app.alerts.anomaly import get_anomalies


@patch("app.alerts.anomaly.get_ce_client")
def test_get_anomalies_success(mock_ce):
    mock_ce.return_value.get_anomalies.return_value = {
        "Anomalies": [{"AnomalyId": "anom-123", "Impact": {"TotalImpact": 100.0}}]
    }
    results = get_anomalies(days=7)
    assert len(results) == 1
    assert results[0]["AnomalyId"] == "anom-123"


@patch("app.alerts.anomaly.get_ce_client")
def test_get_anomalies_failure(mock_ce):
    mock_ce.return_value.get_anomalies.side_effect = Exception("AWS API Error")
    results = get_anomalies(days=7)
    assert results == []
