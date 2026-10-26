"""
Enumerations for the Supplier Reliability Platform.
Covers all lifecycle states, categories, tiers, defect types, risk signals, and anomaly codes.
"""
from enum import Enum


class SupplierTier(str, Enum):
    TIER_1 = "Tier-1"      # Strategic / Direct component manufacturers
    TIER_2 = "Tier-2"      # Sub-tier assemblies & raw material converters
    TIER_3 = "Tier-3"      # Commodity & standard parts suppliers


class SupplierCategory(str, Enum):
    ELECTRONICS = "Electronics"
    PRECISION_MACHINING = "Precision Machining"
    RAW_MATERIALS = "Raw Materials"
    ASSEMBLIES = "Assemblies"
    LOGISTICS = "Logistics"
    PACKAGING = "Packaging"


class SupplierStatus(str, Enum):
    ACTIVE = "Active"
    UNDER_REVIEW = "Under Review"
    SUSPENDED = "Suspended"
    DISQUALIFIED = "Disqualified"


class FinancialStabilityRating(str, Enum):
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"


class FacilityType(str, Enum):
    MANUFACTURING = "Manufacturing"
    ASSEMBLY = "Assembly"
    WAREHOUSE_DEPOT = "Warehouse/Depot"


class SiteStatus(str, Enum):
    OPERATIONAL = "Operational"
    DISRUPTED = "Disrupted"
    MAINTENANCE = "Maintenance"


class ContractType(str, Enum):
    MASTER_SERVICES = "Master Services Agreement"
    FIXED_PRICE = "Fixed Price"
    VOLUME_DISCOUNT = "Volume Discount"


class ContractStatus(str, Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"


class POStatus(str, Enum):
    ISSUED = "Issued"
    CONFIRMED = "Confirmed"
    IN_TRANSIT = "In Transit"
    PARTIALLY_RECEIVED = "Partially Received"
    FULFILLED = "Fulfilled"
    CANCELLED = "Cancelled"


class POLineStatus(str, Enum):
    OPEN = "Open"
    SHIPPED = "Shipped"
    RECEIVED = "Received"
    CANCELLED = "Cancelled"


class ShipmentStatus(str, Enum):
    DISPATCHED = "Dispatched"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    EXCEPTION = "Exception"
    LOST = "Lost"


class TransportMode(str, Enum):
    AIR = "Air"
    OCEAN = "Ocean"
    ROAD = "Road"
    RAIL = "Rail"


class DeliveryEventType(str, Enum):
    PICKUP = "Pickup"
    DEPARTURE = "Departure"
    IN_TRANSIT_SCAN = "In-Transit-Scan"
    CUSTOMS_HOLD = "Customs-Hold"
    ARRIVAL = "Arrival"
    DOCK_RECEIPT = "Dock-Receipt"


class DeliveryStatusCode(str, Enum):
    ON_TIME = "ON_TIME"
    DELAYED = "DELAYED"
    DAMAGED = "DAMAGED"
    HELD = "HELD"


class DefectType(str, Enum):
    NONE = "None"
    DIMENSIONAL = "Dimensional"
    COSMETIC = "Cosmetic"
    FUNCTIONAL = "Functional"
    PACKAGING = "Packaging"


class InspectionDisposition(str, Enum):
    ACCEPTED = "Accepted"
    ACCEPTED_ON_DEVIATION = "Accepted-On-Deviation"
    REJECTED = "Rejected"
    QUARANTINED = "Quarantined"


class InvoicePaymentStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DISPUTED = "Disputed"
    PAID = "Paid"


class InvoiceDisputeReason(str, Enum):
    NONE = "None"
    PRICE_DISCREPANCY = "Price Discrepancy"
    QUANTITY_MISMATCH = "Quantity Mismatch"
    EARLY_INVOICE = "Early Invoice"


class RiskSignalType(str, Enum):
    GEOPOLITICAL = "Geopolitical"
    NATURAL_DISASTER = "Natural Disaster"
    FINANCIAL_DISTRESS = "Financial Distress"
    CYBER_BREACH = "Cyber Breach"
    LABOR_STRIKE = "Labor Strike"
    REGULATORY_NON_COMPLIANCE = "Regulatory Non-Compliance"


class RiskSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskStatus(str, Enum):
    ACTIVE = "Active"
    MITIGATED = "Mitigated"
    FALSE_ALARM = "False Alarm"


class ReliabilityTier(str, Enum):
    TIER_A = "Tier-A"  # 90.0 - 100.0: Preferred Partner
    TIER_B = "Tier-B"  # 80.0 - 89.99: Active / Satisfactory
    TIER_C = "Tier-C"  # 70.0 - 79.99: Active Monitoring
    TIER_D = "Tier-D"  # 60.0 - 69.99: Conditional Review
    TIER_F = "Tier-F"  # < 60.0: Disqualified / Exit


class DecisionRecommendation(str, Enum):
    PREFERRED_PARTNER = "Preferred Partner"
    MAINTAIN_ALLOCATION = "Maintain Allocation"
    ACTIVE_MONITORING = "Active Monitoring"
    CONDITIONAL_REVIEW = "Conditional Review"
    DISQUALIFY_EXIT = "Disqualify / Exit"


class AnomalyCategory(str, Enum):
    ORPHAN_SHIPMENT = "ORPHAN_SHIPMENT"
    TEMPORAL_INVERSION = "TEMPORAL_INVERSION"
    FUTURE_DATA_LEAKAGE = "FUTURE_DATA_LEAKAGE"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    CONFLATED_SITE = "CONFLATED_SITE"
