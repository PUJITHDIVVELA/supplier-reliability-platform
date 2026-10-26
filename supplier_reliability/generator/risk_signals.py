"""
Risk and Disruption Signal Generator.
Generates multi-source disruption signals impacting suppliers: geopolitical, financial,
environmental, labor, cyber, and regulatory.
"""
import random
from datetime import date, datetime, timedelta
from typing import List, Dict

from supplier_reliability.models.entities import Supplier, RiskSignal
from supplier_reliability.models.enums import (
    RiskSignalType,
    RiskSeverity,
    RiskStatus,
)
from supplier_reliability.generator.id_generator import format_risk_signal_id

RISK_SOURCES = [
    "Reuters Supply Chain Monitor",
    "Dun & Bradstreet Risk Analytics",
    "NOAA Severe Weather Alert",
    "Port Authority Congestion Feed",
    "Global Cybersecurity Alert Hub",
    "National Labor Relations Watch",
    "ISO Audit Regulatory Body",
]


def generate_risk_signals(
    suppliers: List[Supplier],
    supplier_archetypes: Dict[str, str],
    target_count: int,
    rng: random.Random,
    start_date: date = date(2026, 1, 1),
    end_date: date = date(2026, 9, 30),
) -> List[RiskSignal]:
    """
    Generates external disruption signals linked to suppliers.
    """
    signals: List[RiskSignal] = []
    signals_per_supplier: Dict[str, int] = {}
    
    # Archetype weights for risk likelihood
    # Deteriorating/QualityProne suppliers receive proportionally more risk signals
    days_span = (end_date - start_date).days

    for _ in range(target_count):
        # Weighted choice of supplier
        sup = rng.choice(suppliers)
        sup_id = sup.supplier_id
        archetype = supplier_archetypes.get(sup_id, "STABLE")

        # Increment signal counter for this supplier
        count = signals_per_supplier.get(sup_id, 0) + 1
        signals_per_supplier[sup_id] = count
        signal_id = format_risk_signal_id(sup_id, count, year=2026)

        sig_type = rng.choice(list(RiskSignalType))

        if archetype == "DETERIORATING":
            severity = rng.choice([RiskSeverity.MEDIUM, RiskSeverity.HIGH, RiskSeverity.CRITICAL])
            confidence = round(rng.uniform(0.75, 0.99), 2)
        elif archetype == "QUALITY_PRONE":
            severity = rng.choice([RiskSeverity.LOW, RiskSeverity.MEDIUM, RiskSeverity.HIGH])
            confidence = round(rng.uniform(0.70, 0.95), 2)
        else:
            severity = rng.choice([RiskSeverity.LOW, RiskSeverity.MEDIUM])
            confidence = round(rng.uniform(0.60, 0.88), 2)

        offset_days = rng.randint(0, days_span)
        det_date = start_date + timedelta(days=offset_days)
        det_dt = datetime(det_date.year, det_date.month, det_date.day, rng.randint(6, 22), rng.randint(0, 59))

        status = RiskStatus.ACTIVE if (end_date - det_date).days < 60 else rng.choice([RiskStatus.MITIGATED, RiskStatus.ACTIVE])

        signal = RiskSignal(
            signal_id=signal_id,
            supplier_id=sup_id,
            signal_type=sig_type,
            severity=severity,
            confidence_score=confidence,
            detected_at=det_dt,
            source=rng.choice(RISK_SOURCES),
            status=status,
        )
        signals.append(signal)

    return signals
