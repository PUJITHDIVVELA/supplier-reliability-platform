"""
Tests for Fixed-Seed Determinism and Reproducibility.
"""
import pytest
from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.config import DEFAULT_SEED


def test_fixed_seed_reproducibility():
    """Confirms running twice with the same seed generates 100% identical data."""
    ds1 = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=True)
    ds2 = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=True)

    # Check identical row counts
    assert len(ds1.suppliers) == len(ds2.suppliers)
    assert len(ds1.sites) == len(ds2.sites)
    assert len(ds1.contracts) == len(ds2.contracts)
    assert len(ds1.purchase_orders) == len(ds2.purchase_orders)
    assert len(ds1.po_lines) == len(ds2.po_lines)
    assert len(ds1.shipments) == len(ds2.shipments)
    assert len(ds1.delivery_events) == len(ds2.delivery_events)
    assert len(ds1.inspections) == len(ds2.inspections)
    assert len(ds1.invoices) == len(ds2.invoices)
    assert len(ds1.risk_signals) == len(ds2.risk_signals)
    assert len(ds1.supplier_scores) == len(ds2.supplier_scores)
    assert len(ds1.ground_truth) == len(ds2.ground_truth)

    # Check exact value match for individual records
    for i in range(len(ds1.suppliers)):
        assert ds1.suppliers[i].supplier_id == ds2.suppliers[i].supplier_id
        assert ds1.suppliers[i].name == ds2.suppliers[i].name

    for i in range(len(ds1.supplier_scores)):
        assert ds1.supplier_scores[i].composite_reliability_score == ds2.supplier_scores[i].composite_reliability_score
        assert ds1.supplier_scores[i].delivery_score == ds2.supplier_scores[i].delivery_score
        assert ds1.supplier_scores[i].quality_score == ds2.supplier_scores[i].quality_score
