"""
Complete Synthetic Data Generation Pipeline.
Coordinates master data, transactions, quality inspections, invoices, risk signals,
multi-signal scoring, and labeled anomaly injection into an end-to-end reproducible workflow.
"""
import random
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Any, Optional

from supplier_reliability.models.entities import (
    Supplier,
    Site,
    Contract,
    PurchaseOrder,
    POLine,
    Shipment,
    DeliveryEvent,
    Inspection,
    Invoice,
    RiskSignal,
    SupplierScore,
)
from supplier_reliability.models.ground_truth import GroundTruthAnomaly
from supplier_reliability.config import (
    SCALE_PROFILES,
    DEFAULT_SEED,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_EDGE_CASE_COUNTS,
)
from supplier_reliability.generator.master_data import generate_master_data
from supplier_reliability.generator.transactions import generate_transactions
from supplier_reliability.generator.risk_signals import generate_risk_signals
from supplier_reliability.generator.edge_cases import inject_edge_cases
from supplier_reliability.generator.id_generator import format_score_id
from supplier_reliability.scoring.formula import compute_supplier_score


@dataclass
class GeneratedDataset:
    suppliers: List[Supplier]
    sites: List[Site]
    contracts: List[Contract]
    purchase_orders: List[PurchaseOrder]
    po_lines: List[POLine]
    shipments: List[Shipment]
    delivery_events: List[DeliveryEvent]
    inspections: List[Inspection]
    invoices: List[Invoice]
    risk_signals: List[RiskSignal]
    supplier_scores: List[SupplierScore]
    ground_truth: List[GroundTruthAnomaly]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, int]:
        return {
            "suppliers": len(self.suppliers),
            "sites": len(self.sites),
            "contracts": len(self.contracts),
            "purchase_orders": len(self.purchase_orders),
            "po_lines": len(self.po_lines),
            "shipments": len(self.shipments),
            "delivery_events": len(self.delivery_events),
            "inspections": len(self.inspections),
            "invoices": len(self.invoices),
            "risk_signals": len(self.risk_signals),
            "supplier_scores": len(self.supplier_scores),
            "ground_truth_anomalies": len(self.ground_truth),
        }


def run_pipeline(
    scale: str = "starter",
    seed: int = DEFAULT_SEED,
    inject_anomalies: bool = True,
    start_date: date = DEFAULT_START_DATE,
    end_date: date = DEFAULT_END_DATE,
) -> GeneratedDataset:
    """
    Executes the deterministic data generation workflow.
    """
    if scale not in SCALE_PROFILES:
        raise ValueError(f"Unknown scale '{scale}'. Available scales: {list(SCALE_PROFILES.keys())}")

    profile = SCALE_PROFILES[scale]
    rng = random.Random(seed)

    # 1. Master Data
    suppliers, sites, contracts, supplier_archetypes = generate_master_data(
        num_suppliers=profile.num_suppliers,
        rng=rng,
        base_date=start_date,
    )

    # 2. Transactions & Events
    purchase_orders, po_lines, shipments, delivery_events, inspections, invoices = generate_transactions(
        suppliers=suppliers,
        sites=sites,
        contracts=contracts,
        supplier_archetypes=supplier_archetypes,
        target_num_pos=profile.num_pos,
        target_num_shipments=profile.num_shipments,
        target_num_inspections=profile.num_inspections,
        rng=rng,
        start_date=start_date,
        end_date=end_date,
    )

    # 3. Disruption Risk Signals
    risk_signals = generate_risk_signals(
        suppliers=suppliers,
        supplier_archetypes=supplier_archetypes,
        target_count=profile.num_risk_signals,
        rng=rng,
        start_date=start_date,
        end_date=end_date,
    )

    # 4. Multi-Signal Scoring Engine (Compute baseline scores for all suppliers)
    eval_timestamp = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    supplier_scores: List[SupplierScore] = []
    
    # Organize lookup dictionaries for fast score aggregation
    sites_by_sup: Dict[str, List[Site]] = {}
    for s in sites:
        sites_by_sup.setdefault(s.supplier_id, []).append(s)

    contracts_by_sup: Dict[str, List[Contract]] = {}
    for c in contracts:
        contracts_by_sup.setdefault(c.supplier_id, []).append(c)

    pos_by_sup: Dict[str, List[PurchaseOrder]] = {}
    for p in purchase_orders:
        pos_by_sup.setdefault(p.supplier_id, []).append(p)

    shps_by_sup: Dict[str, List[Shipment]] = {}
    for shp in shipments:
        shps_by_sup.setdefault(shp.supplier_id, []).append(shp)

    events_by_shp: Dict[str, List[DeliveryEvent]] = {}
    for e in delivery_events:
        events_by_shp.setdefault(e.shipment_id, []).append(e)

    insps_by_sup: Dict[str, List[Inspection]] = {}
    for insp in inspections:
        insps_by_sup.setdefault(insp.supplier_id, []).append(insp)

    invs_by_sup: Dict[str, List[Invoice]] = {}
    for inv in invoices:
        invs_by_sup.setdefault(inv.supplier_id, []).append(inv)

    risks_by_sup: Dict[str, List[RiskSignal]] = {}
    for r in risk_signals:
        risks_by_sup.setdefault(r.supplier_id, []).append(r)

    score_idx = 1
    for sup in suppliers:
        sup_id = sup.supplier_id
        sup_shps = shps_by_sup.get(sup_id, [])
        sup_events = []
        for shp in sup_shps:
            sup_events.extend(events_by_shp.get(shp.shipment_id, []))

        score = compute_supplier_score(
            supplier=sup,
            sites=sites_by_sup.get(sup_id, []),
            contracts=contracts_by_sup.get(sup_id, []),
            purchase_orders=pos_by_sup.get(sup_id, []),
            shipments=sup_shps,
            delivery_events=sup_events,
            inspections=insps_by_sup.get(sup_id, []),
            invoices=invs_by_sup.get(sup_id, []),
            risk_signals=risks_by_sup.get(sup_id, []),
            score_id=format_score_id(score_idx),
            period_start=start_date,
            period_end=end_date,
            evaluation_timestamp=eval_timestamp,
        )
        supplier_scores.append(score)
        score_idx += 1

    # 5. Inject Labeled Edge Cases (if enabled)
    ground_truth: List[GroundTruthAnomaly] = []
    if inject_anomalies:
        scale_ratio = profile.num_suppliers / 1000.0
        edge_counts = {
            k: max(2, int(v * scale_ratio)) for k, v in DEFAULT_EDGE_CASE_COUNTS.items()
        }
        (
            purchase_orders,
            shipments,
            delivery_events,
            risk_signals,
            supplier_scores,
            ground_truth,
        ) = inject_edge_cases(
            suppliers=suppliers,
            sites=sites,
            purchase_orders=purchase_orders,
            shipments=shipments,
            delivery_events=delivery_events,
            risk_signals=risk_signals,
            supplier_scores=supplier_scores,
            edge_case_counts=edge_counts,
            rng=rng,
        )

    metadata = {
        "scale": scale,
        "seed": seed,
        "inject_anomalies": inject_anomalies,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "generated_at": datetime.now().isoformat(),
        "total_entities": 11,
    }

    return GeneratedDataset(
        suppliers=suppliers,
        sites=sites,
        contracts=contracts,
        purchase_orders=purchase_orders,
        po_lines=po_lines,
        shipments=shipments,
        delivery_events=delivery_events,
        inspections=inspections,
        invoices=invoices,
        risk_signals=risk_signals,
        supplier_scores=supplier_scores,
        ground_truth=ground_truth,
        metadata=metadata,
    )
