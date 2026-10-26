"""
Tests for Multi-Signal Scoring Engine and Explainability.
"""
import pytest
from datetime import date, datetime
from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.scoring.formula import compute_supplier_score
from supplier_reliability.config import DEFAULT_SEED, DEFAULT_WEIGHTS


def test_score_bounded_and_explainable():
    """Validates that all scores and subscores are strictly bounded within [0, 100]."""
    dataset = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=False)

    for score in dataset.supplier_scores:
        assert 0.0 <= score.delivery_score <= 100.0
        assert 0.0 <= score.quality_score <= 100.0
        assert 0.0 <= score.cost_score <= 100.0
        assert 0.0 <= score.capacity_score <= 100.0
        assert 0.0 <= score.compliance_score <= 100.0
        assert 0.0 <= score.disruption_penalty <= 100.0
        assert 0.0 <= score.composite_reliability_score <= 100.0

        # Check explainability payload
        exp = score.explainability_summary
        assert "subscores" in exp
        assert "raw_metrics" in exp
        assert "top_drivers" in exp
        assert "primary_drag" in exp["top_drivers"]
        assert "strongest_pillar" in exp["top_drivers"]


def test_missing_data_handled_explicitly():
    """Validates that a supplier with zero history receives a neutral baseline and explicit audit flags."""
    dataset = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=False)
    sup = dataset.suppliers[0]

    # Score with empty delivery, inspection, and invoice history
    score = compute_supplier_score(
        supplier=sup,
        sites=[s for s in dataset.sites if s.supplier_id == sup.supplier_id],
        contracts=[c for c in dataset.contracts if c.supplier_id == sup.supplier_id],
        purchase_orders=[],
        shipments=[],
        delivery_events=[],
        inspections=[],
        invoices=[],
        risk_signals=[],
        score_id="SCORE-TEST-000001",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 9, 30),
        evaluation_timestamp=datetime(2026, 10, 1),
    )

    exp = score.explainability_summary
    assert exp["data_sufficiency_flags"]["insufficient_delivery_data"] is True
    assert exp["data_sufficiency_flags"]["insufficient_quality_data"] is True
    assert exp["data_sufficiency_flags"]["insufficient_cost_data"] is True
    assert score.delivery_score == 75.0
    assert score.quality_score == 80.0
    assert score.cost_score == 85.0
