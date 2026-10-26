"""
Global configuration, scale profiles, and scoring weights for the Supplier Reliability Platform.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict


@dataclass
class ScaleProfile:
    name: str
    num_suppliers: int
    num_pos: int
    num_shipments: int
    num_inspections: int
    num_risk_signals: int


SCALE_PROFILES: Dict[str, ScaleProfile] = {
    "full": ScaleProfile(
        name="full",
        num_suppliers=1000,
        num_pos=10000,
        num_shipments=15000,
        num_inspections=20000,
        num_risk_signals=800,
    ),
    "starter": ScaleProfile(
        name="starter",
        num_suppliers=100,
        num_pos=1000,
        num_shipments=1500,
        num_inspections=2000,
        num_risk_signals=100,
    ),
    "micro": ScaleProfile(
        name="micro",
        num_suppliers=20,
        num_pos=100,
        num_shipments=150,
        num_inspections=200,
        num_risk_signals=25,
    ),
}

DEFAULT_SEED = 20261022

DEFAULT_START_DATE = date(2026, 1, 1)
DEFAULT_END_DATE = date(2026, 10, 22)

# Default Scoring Weights (Must sum to 1.0)
DEFAULT_WEIGHTS = {
    "delivery": 0.25,
    "quality": 0.25,
    "cost": 0.15,
    "capacity": 0.15,
    "compliance": 0.10,
    "disruption": 0.10,
}

# Number of injected instances per mandatory edge case
DEFAULT_EDGE_CASE_COUNTS = {
    "orphan_shipment": 15,          # Shipment has no PO
    "temporal_inversion": 15,       # Delivery date precedes dispatch
    "future_data_leakage": 10,      # Supplier score uses future data
    "missing_provenance": 15,       # Risk signal has no source/time
    "conflated_site": 15,           # Supplier sites are conflated
}
