"""
Reliability Scoring Engine.
Computes multi-pillar explainable scores across Delivery, Quality, Cost, Capacity, Compliance,
and Disruption signals with mathematically clear denominators and explicit missing data handling.
"""
from datetime import date, datetime
from typing import List, Dict, Any, Optional

from supplier_reliability.models.entities import (
    Supplier,
    Site,
    Contract,
    PurchaseOrder,
    Shipment,
    DeliveryEvent,
    Inspection,
    Invoice,
    RiskSignal,
    SupplierScore,
)
from supplier_reliability.models.enums import (
    DeliveryStatusCode,
    DeliveryEventType,
    InspectionDisposition,
    RiskSeverity,
    RiskStatus,
    ReliabilityTier,
    DecisionRecommendation,
)
from supplier_reliability.config import DEFAULT_WEIGHTS
from supplier_reliability.generator.id_generator import format_score_id


def compute_supplier_score(
    supplier: Supplier,
    sites: List[Site],
    contracts: List[Contract],
    purchase_orders: List[PurchaseOrder],
    shipments: List[Shipment],
    delivery_events: List[DeliveryEvent],
    inspections: List[Inspection],
    invoices: List[Invoice],
    risk_signals: List[RiskSignal],
    score_id: str,
    period_start: date,
    period_end: date,
    evaluation_timestamp: datetime,
    weights: Optional[Dict[str, float]] = None,
    allow_future_leakage: bool = False,
) -> SupplierScore:
    """
    Computes explainable reliability scorecard for a single supplier.
    If allow_future_leakage is False, filters out any events occurring after evaluation_timestamp.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    sup_id = supplier.supplier_id

    # Filter events and transactions up to evaluation_timestamp (unless leak is permitted)
    if not allow_future_leakage:
        eval_dt = evaluation_timestamp
        valid_shipments = [s for s in shipments if datetime(s.dispatch_date.year, s.dispatch_date.month, s.dispatch_date.day) <= eval_dt]
        valid_events = [e for e in delivery_events if e.event_timestamp <= eval_dt]
        valid_inspections = [i for i in inspections if datetime(i.inspection_date.year, i.inspection_date.month, i.inspection_date.day) <= eval_dt]
        valid_invoices = [inv for inv in invoices if datetime(inv.invoice_date.year, inv.invoice_date.month, inv.invoice_date.day) <= eval_dt]
        valid_risks = [r for r in risk_signals if r.detected_at is None or r.detected_at <= eval_dt]
    else:
        valid_shipments = shipments
        valid_events = delivery_events
        valid_inspections = inspections
        valid_invoices = invoices
        valid_risks = risk_signals

    # --- 1. DELIVERY SCORE (Clear denominator: Delivered Shipments) ---
    delivered_events = [e for e in valid_events if e.event_type == DeliveryEventType.DOCK_RECEIPT]
    total_delivered_shipments = len(delivered_events)
    on_time_shipments = sum(1 for e in delivered_events if e.status_code == DeliveryStatusCode.ON_TIME)

    insufficient_delivery_data = False
    if total_delivered_shipments > 0:
        on_time_delivery_rate = on_time_shipments / total_delivered_shipments
        total_delivered_units = sum(e.actual_delivered_qty for e in delivered_events)
        total_shipped_units = sum(s.shipped_qty for s in valid_shipments)
        fill_rate = (total_delivered_units / total_shipped_units) if total_shipped_units > 0 else 1.0
        
        # Combined OTD (70%) + Fill Rate (30%)
        delivery_score = round(max(0.0, min(100.0, 100.0 * (0.70 * on_time_delivery_rate + 0.30 * min(1.0, fill_rate)))), 2)
    else:
        # Explicit missing data handling
        insufficient_delivery_data = True
        on_time_delivery_rate = 0.0
        fill_rate = 0.0
        delivery_score = 75.0  # Neutral baseline for suppliers with no delivery history

    # --- 2. QUALITY SCORE (Clear denominator: Total Inspected Units) ---
    total_inspected_units = sum(i.sample_size_inspected for i in valid_inspections)
    total_passed_units = sum(i.units_passed for i in valid_inspections)
    total_defective_units = sum(i.units_defective for i in valid_inspections)

    insufficient_quality_data = False
    if total_inspected_units > 0:
        accept_rate = total_passed_units / total_inspected_units
        aggregate_ppm = (total_defective_units / total_inspected_units) * 1_000_000
        # Quality score scales with pass rate, penalized by ppm
        ppm_penalty = min(40.0, (aggregate_ppm / 1000.0) * 1.5)
        raw_quality = (accept_rate * 100.0) - ppm_penalty
        quality_score = round(max(0.0, min(100.0, raw_quality)), 2)
    else:
        insufficient_quality_data = True
        accept_rate = 1.0
        aggregate_ppm = 0.0
        quality_score = 80.0  # Neutral baseline

    # --- 3. COST & INVOICE ACCURACY (Clear denominator: Total Expected Spend) ---
    total_expected_spend = sum(inv.po_expected_amount for inv in valid_invoices)
    total_invoiced_spend = sum(inv.invoiced_amount for inv in valid_invoices)

    insufficient_cost_data = False
    if total_expected_spend > 0:
        spend_variance = abs(total_invoiced_spend - total_expected_spend) / total_expected_spend
        disputed_invoices_count = sum(1 for inv in valid_invoices if inv.payment_status.value == "Disputed")
        dispute_ratio = disputed_invoices_count / len(valid_invoices)
        
        # Penalize variance above 1% and disputes
        cost_penalty = (spend_variance * 150.0) + (dispute_ratio * 25.0)
        cost_score = round(max(0.0, min(100.0, 100.0 - cost_penalty)), 2)
    else:
        insufficient_cost_data = True
        spend_variance = 0.0
        cost_score = 85.0

    # --- 4. CAPACITY STABILITY (Clear denominator: Total Monthly Site Capacity) ---
    total_site_capacity = sum(s.monthly_capacity_units for s in sites)
    total_utilized_capacity = sum(s.utilized_capacity_units for s in sites)

    if total_site_capacity > 0:
        capacity_utilization = total_utilized_capacity / total_site_capacity
        # Ideal capacity utilization is 60% - 85%
        if 0.55 <= capacity_utilization <= 0.85:
            capacity_score = 98.0
        elif capacity_utilization > 0.85:
            # Overloaded site risk (bottleneck / delay risk)
            over_util = (capacity_utilization - 0.85) / 0.15
            capacity_score = round(max(40.0, 98.0 - (over_util * 45.0)), 2)
        else:
            # Underutilized site (subscale / viability risk)
            under_util = (0.55 - capacity_utilization) / 0.55
            capacity_score = round(max(50.0, 98.0 - (under_util * 35.0)), 2)
    else:
        capacity_utilization = 0.0
        capacity_score = 70.0

    # --- 5. COMPLIANCE & GOVERNANCE ---
    comp_score = 100.0
    # ISO certification check across sites
    uncertified_sites = sum(1 for s in sites if not s.iso_certified)
    if uncertified_sites > 0:
        comp_score -= (uncertified_sites / len(sites)) * 30.0

    # Active contracts check
    active_contracts = sum(1 for c in contracts if c.status.value == "Active")
    if active_contracts == 0:
        comp_score -= 35.0

    compliance_score = round(max(0.0, min(100.0, comp_score)), 2)

    # --- 6. DISRUPTION & RISK SIGNALS ---
    # Severity deductions
    severity_weights = {
        RiskSeverity.CRITICAL: 30.0,
        RiskSeverity.HIGH: 16.0,
        RiskSeverity.MEDIUM: 6.0,
        RiskSeverity.LOW: 2.0,
    }
    
    total_risk_penalty = 0.0
    active_risks = [r for r in valid_risks if r.status == RiskStatus.ACTIVE]
    for r in active_risks:
        base_deduction = severity_weights.get(r.severity, 5.0)
        total_risk_penalty += base_deduction * r.confidence_score

    disruption_penalty = round(min(100.0, total_risk_penalty), 2)
    disruption_score = round(max(0.0, 100.0 - disruption_penalty), 2)

    # --- COMPOSITE RELIABILITY SCORE ---
    composite = (
        weights["delivery"] * delivery_score +
        weights["quality"] * quality_score +
        weights["cost"] * cost_score +
        weights["capacity"] * capacity_score +
        weights["compliance"] * compliance_score +
        weights["disruption"] * disruption_score
    )
    composite = round(max(0.0, min(100.0, composite)), 2)

    # Assign Tier
    if composite >= 90.0:
        tier = ReliabilityTier.TIER_A
        rec = DecisionRecommendation.PREFERRED_PARTNER
    elif composite >= 80.0:
        tier = ReliabilityTier.TIER_B
        rec = DecisionRecommendation.MAINTAIN_ALLOCATION
    elif composite >= 70.0:
        tier = ReliabilityTier.TIER_C
        rec = DecisionRecommendation.ACTIVE_MONITORING
    elif composite >= 60.0:
        tier = ReliabilityTier.TIER_D
        rec = DecisionRecommendation.CONDITIONAL_REVIEW
    else:
        tier = ReliabilityTier.TIER_F
        rec = DecisionRecommendation.DISQUALIFY_EXIT

    # Detailed Explainability Summary
    explainability = {
        "supplier_id": sup_id,
        "composite_reliability_score": composite,
        "tier": tier.value,
        "recommendation": rec.value,
        "weights": weights,
        "subscores": {
            "delivery": delivery_score,
            "quality": quality_score,
            "cost": cost_score,
            "capacity": capacity_score,
            "compliance": compliance_score,
            "disruption": disruption_score,
        },
        "raw_metrics": {
            "total_delivered_shipments": total_delivered_shipments,
            "on_time_shipments": on_time_shipments,
            "on_time_rate_pct": round(on_time_delivery_rate * 100.0, 2),
            "total_inspected_units": total_inspected_units,
            "defect_ppm": round(aggregate_ppm, 1),
            "accept_rate_pct": round(accept_rate * 100.0, 2),
            "spend_variance_pct": round(spend_variance * 100.0, 2),
            "capacity_utilization_pct": round(capacity_utilization * 100.0, 2),
            "active_risk_signal_count": len(active_risks),
            "disruption_penalty_points": disruption_penalty,
        },
        "data_sufficiency_flags": {
            "insufficient_delivery_data": insufficient_delivery_data,
            "insufficient_quality_data": insufficient_quality_data,
            "insufficient_cost_data": insufficient_cost_data,
        },
        "top_drivers": _identify_top_drivers(delivery_score, quality_score, cost_score, capacity_score, compliance_score, disruption_score)
    }

    return SupplierScore(
        score_id=score_id,
        supplier_id=sup_id,
        score_period_start=period_start,
        score_period_end=period_end,
        evaluation_timestamp=evaluation_timestamp,
        delivery_score=delivery_score,
        quality_score=quality_score,
        cost_score=cost_score,
        capacity_score=capacity_score,
        compliance_score=compliance_score,
        disruption_penalty=disruption_penalty,
        composite_reliability_score=composite,
        reliability_tier=tier,
        decision_recommendation=rec,
        explainability_summary=explainability,
        is_future_data_leakage=allow_future_leakage,
    )


def _identify_top_drivers(del_s: float, qual_s: float, cost_s: float, cap_s: float, comp_s: float, dis_s: float) -> Dict[str, Any]:
    scores = {
        "delivery": del_s,
        "quality": qual_s,
        "cost": cost_s,
        "capacity": cap_s,
        "compliance": comp_s,
        "disruption": dis_s,
    }
    sorted_scores = sorted(scores.items(), key=lambda x: x[1])
    return {
        "primary_drag": sorted_scores[0],  # lowest scoring pillar
        "secondary_drag": sorted_scores[1],
        "strongest_pillar": sorted_scores[-1],
    }
