"""
Deterministic, zero-padded, immutable ID generation conforming strictly to
the business specification.
"""

def format_supplier_id(index: int) -> str:
    """Format: SUP-000001 (6 digits zero-padded)"""
    return f"SUP-{index:06d}"


def format_site_id(supplier_id: str, site_num: int) -> str:
    """Format: SITE-<supplier-id>-01"""
    return f"SITE-{supplier_id}-{site_num:02d}"


def format_contract_id(index: int, year: int = 2026) -> str:
    """Format: CTR-2026-000001"""
    return f"CTR-{year}-{index:06d}"


def format_po_id(index: int, year: int = 2026) -> str:
    """Format: PO-2026-000001"""
    return f"PO-{year}-{index:06d}"


def format_po_line_id(po_id: str, line_num: int) -> str:
    """Format: POL-PO-2026-000001-01"""
    return f"POL-{po_id}-{line_num:02d}"


def format_shipment_id(index: int, year: int = 2026) -> str:
    """Format: SHP-2026-000001"""
    return f"SHP-{year}-{index:06d}"


def format_event_id(index: int, year: int = 2026) -> str:
    """Format: EVT-2026-000001"""
    return f"EVT-{year}-{index:06d}"


def format_inspection_id(index: int, year: int = 2026) -> str:
    """Format: INS-2026-000001"""
    return f"INS-{year}-{index:06d}"


def format_invoice_id(index: int, year: int = 2026) -> str:
    """Format: INV-2026-000001"""
    return f"INV-{year}-{index:06d}"


def format_risk_signal_id(supplier_id: str, signal_num: int, year: int = 2026) -> str:
    """Format: RSK-<supplier-id>-2026-01"""
    return f"RSK-{supplier_id}-{year}-{signal_num:02d}"


def format_score_id(index: int, year: int = 2026) -> str:
    """Format: SCORE-2026-000001"""
    return f"SCORE-{year}-{index:06d}"


def format_ground_truth_id(index: int) -> str:
    """Format: GT-000001"""
    return f"GT-{index:06d}"
