"""
Tests for Edge Cases and Ground Truth Non-Leakage.
"""
import pytest
from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.models.enums import AnomalyCategory
from supplier_reliability.config import DEFAULT_SEED


def test_all_five_edge_cases_present_in_ground_truth():
    """Verifies all 5 mandated edge cases are properly injected and recorded in ground truth."""
    dataset = run_pipeline(scale="starter", seed=DEFAULT_SEED, inject_anomalies=True)

    gt_categories = {gt.anomaly_category for gt in dataset.ground_truth}

    assert AnomalyCategory.ORPHAN_SHIPMENT in gt_categories
    assert AnomalyCategory.TEMPORAL_INVERSION in gt_categories
    assert AnomalyCategory.FUTURE_DATA_LEAKAGE in gt_categories
    assert AnomalyCategory.MISSING_PROVENANCE in gt_categories
    assert AnomalyCategory.CONFLATED_SITE in gt_categories


def test_no_ground_truth_leakage_into_operational_features():
    """Confirms operational entity models do not contain ground truth classification labels."""
    dataset = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=True)

    # Check Shipment model fields
    shipment_fields = dataset.shipments[0].model_dump().keys()
    assert "anomaly_category" not in shipment_fields
    assert "ground_truth_label" not in shipment_fields
    assert "is_anomaly" not in shipment_fields

    # Check DeliveryEvent model fields
    event_fields = dataset.delivery_events[0].model_dump().keys()
    assert "anomaly_category" not in event_fields

    # Check PurchaseOrder model fields
    po_fields = dataset.purchase_orders[0].model_dump().keys()
    assert "anomaly_category" not in po_fields

    # Check RiskSignal model fields
    risk_fields = dataset.risk_signals[0].model_dump().keys()
    assert "anomaly_category" not in risk_fields
