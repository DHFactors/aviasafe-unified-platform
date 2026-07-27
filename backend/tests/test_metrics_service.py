from app.services.metrics_service import MetricsService


def test_calculate_kpis_empty():
    result = MetricsService.calculate_kpis([])
    assert result["total_reports"] == 0
    assert result["open_reports"] == 0
    assert result["high_risk_reports"] == 0
    assert result["anonymous_percentage"] == 0.0


def test_calculate_kpis_with_data(sample_reports):
    result = MetricsService.calculate_kpis(sample_reports)
    assert result["total_reports"] == 2
    assert result["open_reports"] == 1
    assert result["closed_reports"] == 1
    assert result["high_risk_reports"] == 1
    assert result["anonymous_percentage"] == 50.0


def test_calculate_risk_distribution(sample_reports):
    result = MetricsService.calculate_risk_distribution(sample_reports)
    levels = {r["risk_level"]: r["count"] for r in result}
    assert levels.get("Low") == 1
    assert levels.get("High") == 1
    assert levels.get("Critical") == 0
    assert sum(r["count"] for r in result) == 2


def test_calculate_hazard_frequency(sample_reports):
    result = MetricsService.calculate_hazard_frequency(sample_reports)
    types = {r["occurrence_type"]: r["count"] for r in result}
    assert types.get("Bird Strike") == 1


def test_calculate_monthly_trends(sample_reports):
    result = MetricsService.calculate_monthly_trends(sample_reports)
    assert len(result) >= 1
    assert result[0]["total"] == 2


def test_calculate_ai_kpis(sample_reports):
    result = MetricsService.calculate_ai_kpis(sample_reports)
    assert result["ai_processed"] == 1
    assert result["ai_pending"] == 1


def test_calculate_org_kpis(sample_reports):
    result = MetricsService.calculate_org_kpis(sample_reports)
    assert result["active_reporters"] == 2
    assert result["corrective_actions_open"] == 1
    assert result["investigation_backlog"] == 1
