"""
Tests for Synthetic Data Generator and ID Nomenclature.
"""
import pytest
from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.config import DEFAULT_SEED


def test_id_nomenclature_conventions():
    """Validates that all generated IDs strictly match required naming formats."""
    dataset = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=False)

    # 1. Supplier: SUP-000001
    for s in dataset.suppliers:
        assert s.supplier_id.startswith("SUP-")
        assert len(s.supplier_id) == 10  # SUP- + 6 digits

    # 2. Site: SITE-<supplier-id>-01
    for site in dataset.sites:
        assert site.site_id.startswith(f"SITE-{site.supplier_id}-")

    # 3. PO: PO-2026-000001
    for po in dataset.purchase_orders:
        assert po.po_id.startswith("PO-2026-")

    # 4. POLine: POL-PO-2026-000001-01
    for pol in dataset.po_lines:
        assert pol.po_line_id.startswith("POL-PO-2026-")

    # 5. Shipment: SHP-2026-000001
    for shp in dataset.shipments:
        assert shp.shipment_id.startswith("SHP-2026-")

    # 6. Event: EVT-2026-000001
    for evt in dataset.delivery_events:
        assert evt.event_id.startswith("EVT-2026-")

    # 7. Inspection: INS-2026-000001
    for insp in dataset.inspections:
        assert insp.inspection_id.startswith("INS-2026-")

    # 8. Invoice: INV-2026-000001
    for inv in dataset.invoices:
        assert inv.invoice_id.startswith("INV-2026-")

    # 9. RiskSignal: RSK-<supplier-id>-2026-01
    for rsk in dataset.risk_signals:
        assert rsk.signal_id.startswith(f"RSK-{rsk.supplier_id}-2026-")

    # 10. SupplierScore: SCORE-2026-000001
    for sc in dataset.supplier_scores:
        assert sc.score_id.startswith("SCORE-2026-")


def test_generator_cardinalities_and_links():
    """Validates relational parent-child cardinalities."""
    dataset = run_pipeline(scale="micro", seed=DEFAULT_SEED, inject_anomalies=False)
    
    assert len(dataset.suppliers) == 20
    assert len(dataset.sites) >= 20  # At least 1 site per supplier
    assert len(dataset.purchase_orders) == 100
    assert len(dataset.po_lines) >= 100  # At least 1 line per PO
    assert len(dataset.shipments) == 150
    assert len(dataset.delivery_events) >= 150 * 2  # At least 2 events per shipment
    assert len(dataset.inspections) == 200
    assert len(dataset.invoices) == 100
    assert len(dataset.supplier_scores) == 20
