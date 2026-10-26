"""
Edge Case and Anomaly Injection Engine.
Deterministically injects the 5 mandated edge cases into baseline data:
1. Shipment has no PO (orphan shipment)
2. Delivery date precedes dispatch (temporal inversion)
3. Supplier score uses future data (data leakage)
4. Risk signal has no source/time (missing provenance)
5. Supplier sites are conflated (site tenancy mismatch)

Produces an isolated ground_truth dataset without leaking labels into operational features.
"""
import random
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

from supplier_reliability.models.entities import (
    Supplier,
    Site,
    PurchaseOrder,
    Shipment,
    DeliveryEvent,
    RiskSignal,
    SupplierScore,
)
from supplier_reliability.models.ground_truth import GroundTruthAnomaly
from supplier_reliability.models.enums import (
    AnomalyCategory,
    DeliveryEventType,
)
from supplier_reliability.generator.id_generator import format_ground_truth_id


def inject_edge_cases(
    suppliers: List[Supplier],
    sites: List[Site],
    purchase_orders: List[PurchaseOrder],
    shipments: List[Shipment],
    delivery_events: List[DeliveryEvent],
    risk_signals: List[RiskSignal],
    supplier_scores: List[SupplierScore],
    edge_case_counts: Dict[str, int],
    rng: random.Random,
) -> Tuple[
    List[PurchaseOrder],
    List[Shipment],
    List[DeliveryEvent],
    List[RiskSignal],
    List[SupplierScore],
    List[GroundTruthAnomaly],
]:
    """
    Applies deterministic anomalies in-place and returns the isolated ground truth labels.
    """
    ground_truth_records: List[GroundTruthAnomaly] = []
    gt_counter = 1

    # Map sites by supplier
    sites_by_supplier: Dict[str, List[Site]] = {}
    for s in sites:
        sites_by_supplier.setdefault(s.supplier_id, []).append(s)

    # 1. Edge Case: Shipment has no PO (Orphan shipment)
    num_orphan_shps = min(edge_case_counts.get("orphan_shipment", 15), len(shipments))
    orphan_shp_indices = rng.sample(range(len(shipments)), num_orphan_shps)
    for idx in orphan_shp_indices:
        shp = shipments[idx]
        original_po = shp.po_id
        # Detach PO
        shp.po_id = None
        
        gt = GroundTruthAnomaly(
            ground_truth_id=format_ground_truth_id(gt_counter),
            entity_type="Shipment",
            record_id=shp.shipment_id,
            anomaly_category=AnomalyCategory.ORPHAN_SHIPMENT,
            audit_rule_violated="FK_PO_NULL",
            severity="Critical",
            expected_action="Quarantine shipment and reject automated dock receipt until PO reconciled",
            description=f"Shipment {shp.shipment_id} has null PO link (previously referenced {original_po}).",
            created_at=datetime(2026, 10, 22, 12, 0),
        )
        ground_truth_records.append(gt)
        gt_counter += 1

    # 2. Edge Case: Delivery date precedes dispatch (Temporal inversion)
    # Find dock-receipt delivery events
    dock_events = [
        (idx, e) for idx, e in enumerate(delivery_events)
        if e.event_type == DeliveryEventType.DOCK_RECEIPT
    ]
    num_temporal = min(edge_case_counts.get("temporal_inversion", 15), len(dock_events))
    chosen_dock_events = rng.sample(dock_events, num_temporal)
    
    # Map shipment by id for quick lookup
    shipment_by_id = {s.shipment_id: s for s in shipments}

    for idx, evt in chosen_dock_events:
        parent_shp = shipment_by_id.get(evt.shipment_id)
        if parent_shp:
            # Set event timestamp 3 to 7 days BEFORE shipment dispatch date
            inverted_dt = datetime(
                parent_shp.dispatch_date.year,
                parent_shp.dispatch_date.month,
                parent_shp.dispatch_date.day,
                8,
                30
            ) - timedelta(days=rng.randint(2, 6))
            
            evt.event_timestamp = inverted_dt
            evt.notes = "Inverted timestamp anomaly (carrier system clock desynchronization)"

            gt = GroundTruthAnomaly(
                ground_truth_id=format_ground_truth_id(gt_counter),
                entity_type="DeliveryEvent",
                record_id=evt.event_id,
                anomaly_category=AnomalyCategory.TEMPORAL_INVERSION,
                audit_rule_violated="DELIVERY_BEFORE_DISPATCH",
                severity="Critical",
                expected_action="Flag for carrier audit; invalidate receipt timestamp for SLA computation",
                description=(
                    f"DeliveryEvent {evt.event_id} timestamp ({evt.event_timestamp.date()}) "
                    f"precedes dispatch date ({parent_shp.dispatch_date})."
                ),
                created_at=datetime(2026, 10, 22, 12, 0),
            )
            ground_truth_records.append(gt)
            gt_counter += 1

    # 3. Edge Case: Supplier score uses future data (Data Leakage)
    num_future_leak = min(edge_case_counts.get("future_data_leakage", 10), len(supplier_scores))
    future_score_indices = rng.sample(range(len(supplier_scores)), num_future_leak)
    for idx in future_score_indices:
        score = supplier_scores[idx]
        # Rewind score's evaluation_timestamp to March 2026, while the score was computed
        # using events occurring all the way to September 2026!
        score.evaluation_timestamp = datetime(2026, 3, 1, 9, 0, 0)
        score.is_future_data_leakage = True
        
        gt = GroundTruthAnomaly(
            ground_truth_id=format_ground_truth_id(gt_counter),
            entity_type="SupplierScore",
            record_id=score.score_id,
            anomaly_category=AnomalyCategory.FUTURE_DATA_LEAKAGE,
            audit_rule_violated="TIMESTAMP_LEAKAGE",
            severity="High",
            expected_action="Re-run score calculation strictly with historical point-in-time snapshot",
            description=(
                f"SupplierScore {score.score_id} has evaluation_timestamp 2026-03-01 "
                f"but incorporates transactions dated up to 2026-09-30."
            ),
            created_at=datetime(2026, 10, 22, 12, 0),
        )
        ground_truth_records.append(gt)
        gt_counter += 1

    # 4. Edge Case: Risk signal has no source/time (Missing provenance)
    num_missing_prov = min(edge_case_counts.get("missing_provenance", 15), len(risk_signals))
    missing_prov_indices = rng.sample(range(len(risk_signals)), num_missing_prov)
    for idx in missing_prov_indices:
        risk = risk_signals[idx]
        risk.source = None
        risk.detected_at = None

        gt = GroundTruthAnomaly(
            ground_truth_id=format_ground_truth_id(gt_counter),
            entity_type="RiskSignal",
            record_id=risk.signal_id,
            anomaly_category=AnomalyCategory.MISSING_PROVENANCE,
            audit_rule_violated="NULL_PROVENANCE",
            severity="Medium",
            expected_action="Reject unverified risk signal from reliability calculation until source verified",
            description=f"RiskSignal {risk.signal_id} is missing both intelligence source and detection timestamp.",
            created_at=datetime(2026, 10, 22, 12, 0),
        )
        ground_truth_records.append(gt)
        gt_counter += 1

    # 5. Edge Case: Supplier sites are conflated (Cross-supplier site mismatch)
    # Assign a site from Supplier B to a PO of Supplier A
    num_conflated = min(edge_case_counts.get("conflated_site", 15), len(purchase_orders))
    conflated_po_indices = rng.sample(range(len(purchase_orders)), num_conflated)
    
    all_suppliers_list = [s.supplier_id for s in suppliers]

    for idx in conflated_po_indices:
        po = purchase_orders[idx]
        # Pick another supplier
        other_suppliers = [sid for sid in all_suppliers_list if sid != po.supplier_id]
        if other_suppliers:
            other_sup = rng.choice(other_suppliers)
            other_sites = sites_by_supplier.get(other_sup, [])
            if other_sites:
                foreign_site = rng.choice(other_sites)
                original_site = po.site_id
                po.site_id = foreign_site.site_id

                gt = GroundTruthAnomaly(
                    ground_truth_id=format_ground_truth_id(gt_counter),
                    entity_type="PurchaseOrder",
                    record_id=po.po_id,
                    anomaly_category=AnomalyCategory.CONFLATED_SITE,
                    audit_rule_violated="SITE_TENANCY_MISMATCH",
                    severity="Critical",
                    expected_action="Reject PO issuance; site does not belong to contracted supplier",
                    description=(
                        f"PurchaseOrder {po.po_id} for Supplier {po.supplier_id} was assigned "
                        f"site {foreign_site.site_id} belonging to foreign Supplier {other_sup} (was {original_site})."
                    ),
                    created_at=datetime(2026, 10, 22, 12, 0),
                )
                ground_truth_records.append(gt)
                gt_counter += 1

    return purchase_orders, shipments, delivery_events, risk_signals, supplier_scores, ground_truth_records
