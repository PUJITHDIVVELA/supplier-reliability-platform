"""
Ground Truth entity definition for deliberate anomalies and expected audit outcomes.
Persisted in a standalone file (ground_truth.csv / ground_truth.json) and strictly
kept isolated from input operational features to avoid leakage.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from supplier_reliability.models.enums import AnomalyCategory


class GroundTruthAnomaly(BaseModel):
    """
    Ground truth label for injected edge cases and anomalies.
    """
    ground_truth_id: str = Field(..., description="Unique ID, e.g. GT-000001")
    entity_type: str = Field(..., description="Target entity table name, e.g. Shipment, DeliveryEvent")
    record_id: str = Field(..., description="Target record primary key")
    anomaly_category: AnomalyCategory = Field(...)
    audit_rule_violated: str = Field(..., description="Formal rule identifier violated")
    severity: str = Field(default="Critical")
    expected_action: str = Field(..., description="Expected system/analyst action")
    description: str = Field(..., description="Explanation of why this record is anomalous")
    created_at: datetime = Field(...)
