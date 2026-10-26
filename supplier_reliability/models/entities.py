"""
Core relational entity schemas for the Supplier Reliability Platform.
All 11 entities are explicitly modeled with primary keys, foreign keys,
cardinalities, lifecycle states, and validation rules.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from supplier_reliability.models.enums import (
    SupplierTier,
    SupplierCategory,
    SupplierStatus,
    FinancialStabilityRating,
    FacilityType,
    SiteStatus,
    ContractType,
    ContractStatus,
    POStatus,
    POLineStatus,
    ShipmentStatus,
    TransportMode,
    DeliveryEventType,
    DeliveryStatusCode,
    DefectType,
    InspectionDisposition,
    InvoicePaymentStatus,
    InvoiceDisputeReason,
    RiskSignalType,
    RiskSeverity,
    RiskStatus,
    ReliabilityTier,
    DecisionRecommendation,
)


class Supplier(BaseModel):
    """
    Master Supplier Entity.
    Cardinality: 1 Supplier -> N Sites, 1 Supplier -> N Contracts, 1 Supplier -> N POs.
    """
    supplier_id: str = Field(..., description="Primary Key, format SUP-000001")
    name: str = Field(..., description="Company legal name")
    tier: SupplierTier = Field(..., description="Supplier classification tier")
    category: SupplierCategory = Field(..., description="Commodity / Service Category")
    status: SupplierStatus = Field(default=SupplierStatus.ACTIVE)
    country: str = Field(..., description="ISO 3166-1 alpha-2 or standard country name")
    founded_year: int = Field(..., description="Year established")
    financial_stability_rating: FinancialStabilityRating = Field(...)
    created_at: datetime = Field(...)


class Site(BaseModel):
    """
    Supplier Manufacturing or Distribution Site.
    Cardinality: N Sites -> 1 Supplier; 1 Site -> N Shipments/POs.
    """
    site_id: str = Field(..., description="Primary Key, format SITE-<supplier-id>-01")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    site_name: str = Field(...)
    country: str = Field(...)
    city: str = Field(...)
    address: str = Field(...)
    facility_type: FacilityType = Field(...)
    monthly_capacity_units: int = Field(..., ge=0, description="Rated monthly capacity in units")
    utilized_capacity_units: int = Field(..., ge=0, description="Current committed monthly capacity")
    iso_certified: bool = Field(default=True, description="Whether site holds ISO 9001/14001 certification")
    status: SiteStatus = Field(default=SiteStatus.OPERATIONAL)
    created_at: datetime = Field(...)


class Contract(BaseModel):
    """
    Legal agreement establishing commercial and SLA parameters.
    Cardinality: N Contracts -> 1 Supplier; 1 Contract -> N POs.
    """
    contract_id: str = Field(..., description="Primary Key, format CTR-2026-000001")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    contract_type: ContractType = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)
    agreed_sla_otd_pct: float = Field(..., ge=0.0, le=100.0, description="Agreed On-Time Delivery % target")
    agreed_defect_ppm_threshold: int = Field(..., ge=0, description="Maximum acceptable defect PPM")
    unit_price_ceiling: float = Field(..., gt=0.0, description="Ceiling unit price in USD")
    payment_terms: str = Field(default="Net 30")
    status: ContractStatus = Field(default=ContractStatus.ACTIVE)


class PurchaseOrder(BaseModel):
    """
    Commercial purchase order issued to a supplier site.
    Cardinality: 1 PO -> N POLines; 1 PO -> N Shipments; 1 PO -> N Invoices.
    """
    po_id: str = Field(..., description="Primary Key, format PO-2026-000001")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    contract_id: str = Field(..., description="Foreign Key -> Contract.contract_id")
    site_id: str = Field(..., description="Foreign Key -> Site.site_id (fulfilling site)")
    po_date: date = Field(...)
    required_delivery_date: date = Field(...)
    total_amount: float = Field(..., ge=0.0, description="Sum of line item totals in USD")
    currency: str = Field(default="USD")
    status: POStatus = Field(default=POStatus.ISSUED)
    buyer_id: str = Field(..., description="Internal planner/procurement officer ID")
    created_at: datetime = Field(...)


class POLine(BaseModel):
    """
    Line item belonging to a Purchase Order.
    Cardinality: N POLines -> 1 PO.
    """
    po_line_id: str = Field(..., description="Primary Key, format POL-PO-2026-000001-01")
    po_id: str = Field(..., description="Foreign Key -> PurchaseOrder.po_id")
    line_number: int = Field(..., ge=1)
    item_sku: str = Field(...)
    description: str = Field(...)
    ordered_qty: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0.0)
    line_total: float = Field(..., ge=0.0, description="Reconciled ordered_qty * unit_price")
    required_date: date = Field(...)
    cancelled_qty: int = Field(default=0, ge=0)
    status: POLineStatus = Field(default=POLineStatus.OPEN)


class Shipment(BaseModel):
    """
    Physical shipment dispatched to fulfill one (or part of a) PO.
    Cardinality: 1 Shipment -> N DeliveryEvents; 1 Shipment -> N Inspections.
    Note: po_id is Optional to allow modeling deliberate edge case: 'Shipment has no PO'.
    """
    shipment_id: str = Field(..., description="Primary Key, format SHP-2026-000001")
    po_id: Optional[str] = Field(None, description="Foreign Key -> PurchaseOrder.po_id (NULL in orphan edge cases)")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    origin_site_id: str = Field(..., description="Foreign Key -> Site.site_id")
    carrier_code: str = Field(..., description="Carrier code (DHL, FEDEX, MAERSK, etc.)")
    tracking_number: str = Field(...)
    dispatch_date: date = Field(...)
    estimated_delivery_date: date = Field(...)
    shipped_qty: int = Field(..., ge=0)
    mode: TransportMode = Field(...)
    status: ShipmentStatus = Field(default=ShipmentStatus.DISPATCHED)


class DeliveryEvent(BaseModel):
    """
    Discrete logistics audit event along the transit and delivery lifecycle.
    Cardinality: N DeliveryEvents -> 1 Shipment.
    """
    event_id: str = Field(..., description="Primary Key, format EVT-2026-000001")
    shipment_id: str = Field(..., description="Foreign Key -> Shipment.shipment_id")
    event_type: DeliveryEventType = Field(...)
    event_timestamp: datetime = Field(...)
    location: str = Field(...)
    status_code: DeliveryStatusCode = Field(...)
    actual_delivered_qty: int = Field(default=0, ge=0)
    received_by: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)


class Inspection(BaseModel):
    """
    Incoming Quality Control inspection performed on received shipment goods.
    Cardinality: N Inspections -> 1 Shipment.
    """
    inspection_id: str = Field(..., description="Primary Key, format INS-2026-000001")
    shipment_id: str = Field(..., description="Foreign Key -> Shipment.shipment_id")
    po_id: Optional[str] = Field(None, description="Foreign Key -> PurchaseOrder.po_id")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    inspection_date: date = Field(...)
    sample_size_inspected: int = Field(..., gt=0)
    units_passed: int = Field(..., ge=0)
    units_defective: int = Field(..., ge=0)
    defect_type: DefectType = Field(default=DefectType.NONE)
    defect_ppm: float = Field(..., ge=0.0, description="Calculated (units_defective / sample_size) * 1M")
    disposition: InspectionDisposition = Field(...)
    inspector_id: str = Field(...)


class Invoice(BaseModel):
    """
    Commercial invoice submitted by supplier for PO payment.
    Cardinality: N Invoices -> 1 PO; N Invoices -> 1 Supplier.
    """
    invoice_id: str = Field(..., description="Primary Key, format INV-2026-000001")
    po_id: str = Field(..., description="Foreign Key -> PurchaseOrder.po_id")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    invoice_date: date = Field(...)
    due_date: date = Field(...)
    invoiced_amount: float = Field(..., ge=0.0)
    po_expected_amount: float = Field(..., ge=0.0)
    cost_variance_pct: float = Field(..., description="((invoiced - expected) / expected) * 100")
    payment_status: InvoicePaymentStatus = Field(default=InvoicePaymentStatus.PENDING)
    dispute_reason: InvoiceDisputeReason = Field(default=InvoiceDisputeReason.NONE)


class RiskSignal(BaseModel):
    """
    External and internal risk signal impacting supplier reliability.
    Cardinality: N RiskSignals -> 1 Supplier.
    Note: detected_at and source are Optional to allow edge case: 'Risk signal has no source/time'.
    """
    signal_id: str = Field(..., description="Primary Key, format RSK-<supplier-id>-2026-01")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    signal_type: RiskSignalType = Field(...)
    severity: RiskSeverity = Field(...)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detected_at: Optional[datetime] = Field(None, description="Timestamp of detection. Null in provenance edge cases")
    source: Optional[str] = Field(None, description="Intelligence source. Null in provenance edge cases")
    status: RiskStatus = Field(default=RiskStatus.ACTIVE)


class SupplierScore(BaseModel):
    """
    Multi-pillar composite reliability scorecard with explainable sub-scores.
    Cardinality: N SupplierScores -> 1 Supplier (over time).
    """
    score_id: str = Field(..., description="Primary Key, format SCORE-2026-000001")
    supplier_id: str = Field(..., description="Foreign Key -> Supplier.supplier_id")
    score_period_start: date = Field(...)
    score_period_end: date = Field(...)
    evaluation_timestamp: datetime = Field(...)
    
    # 6 Pillar Sub-scores (0.00 to 100.00)
    delivery_score: float = Field(..., ge=0.0, le=100.0)
    quality_score: float = Field(..., ge=0.0, le=100.0)
    cost_score: float = Field(..., ge=0.0, le=100.0)
    capacity_score: float = Field(..., ge=0.0, le=100.0)
    compliance_score: float = Field(..., ge=0.0, le=100.0)
    disruption_penalty: float = Field(..., ge=0.0, le=100.0, description="Deduction or penalty score (0 to 100)")
    
    # Composite Score & Decisions
    composite_reliability_score: float = Field(..., ge=0.0, le=100.0)
    reliability_tier: ReliabilityTier = Field(...)
    decision_recommendation: DecisionRecommendation = Field(...)
    
    # Explainability & Audit Flags
    explainability_summary: Dict[str, Any] = Field(default_factory=dict)
    is_future_data_leakage: bool = Field(default=False, description="Flagged true if evaluation uses future data")
