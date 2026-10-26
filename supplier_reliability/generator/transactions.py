"""
Transaction and Event Data Generator.
Generates PurchaseOrders, POLines, Shipments, DeliveryEvents, Inspections, and Invoices.
Ensures strict parent-child referential validity and derived value reconciliation.
"""
import random
from datetime import date, datetime, timedelta
from typing import List, Tuple, Dict

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
)
from supplier_reliability.models.enums import (
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
)
from supplier_reliability.generator.id_generator import (
    format_po_id,
    format_po_line_id,
    format_shipment_id,
    format_event_id,
    format_inspection_id,
    format_invoice_id,
)

CARRIERS = ["DHL Express", "FedEx Supply Chain", "Maersk Logistics", "UPS Freight", "DB Schenker", "Kuehne+Nagel"]
BUYERS = ["BYR-101 (J. Miller)", "BYR-104 (A. Chen)", "BYR-109 (S. Patel)", "BYR-112 (E. Rossi)"]
INSPECTORS = ["QC-801", "QC-804", "QC-809", "QC-812", "QC-818"]


def generate_transactions(
    suppliers: List[Supplier],
    sites: List[Site],
    contracts: List[Contract],
    supplier_archetypes: Dict[str, str],
    target_num_pos: int,
    target_num_shipments: int,
    target_num_inspections: int,
    rng: random.Random,
    start_date: date = date(2026, 1, 1),
    end_date: date = date(2026, 9, 30),
) -> Tuple[
    List[PurchaseOrder],
    List[POLine],
    List[Shipment],
    List[DeliveryEvent],
    List[Inspection],
    List[Invoice],
]:
    """
    Generates relational transaction entities conforming to business logic.
    """
    # Group sites and contracts by supplier
    sites_by_supplier: Dict[str, List[Site]] = {}
    for s in sites:
        sites_by_supplier.setdefault(s.supplier_id, []).append(s)

    contracts_by_supplier: Dict[str, List[Contract]] = {}
    for c in contracts:
        contracts_by_supplier.setdefault(c.supplier_id, []).append(c)

    # Separate low volume suppliers from regular
    active_suppliers = [
        s for s in suppliers if supplier_archetypes.get(s.supplier_id) != "LOW_VOLUME"
    ]
    low_volume_suppliers = [
        s for s in suppliers if supplier_archetypes.get(s.supplier_id) == "LOW_VOLUME"
    ]

    purchase_orders: List[PurchaseOrder] = []
    po_lines: List[POLine] = []
    shipments: List[Shipment] = []
    delivery_events: List[DeliveryEvent] = []
    inspections: List[Inspection] = []
    invoices: List[Invoice] = []

    event_counter = 1
    shipment_counter = 1
    inspection_counter = 1
    invoice_counter = 1

    # Generate POs
    days_span = (end_date - start_date).days

    for po_idx in range(1, target_num_pos + 1):
        po_id = format_po_id(po_idx)
        
        # 98% of POs go to active suppliers, 2% to low volume suppliers
        if low_volume_suppliers and rng.random() < 0.02:
            sup = rng.choice(low_volume_suppliers)
        else:
            sup = rng.choice(active_suppliers)

        sup_id = sup.supplier_id
        sup_sites = sites_by_supplier[sup_id]
        sup_contracts = contracts_by_supplier[sup_id]

        fulfilling_site = rng.choice(sup_sites)
        applied_contract = rng.choice(sup_contracts)
        archetype = supplier_archetypes.get(sup_id, "STABLE")

        po_day_offset = rng.randint(0, days_span)
        po_date = start_date + timedelta(days=po_day_offset)

        # Baseline lead time based on archetype
        if archetype == "DETERIORATING":
            # Deteriorating lead time
            lead_time_days = rng.randint(28, 60)
        else:
            lead_time_days = rng.randint(14, 30)

        required_date = po_date + timedelta(days=lead_time_days)

        # Generate 1 to 3 PO lines
        num_lines = rng.randint(1, 3)
        po_total = 0.0
        po_lines_for_this_po = []

        for l_num in range(1, num_lines + 1):
            line_id = format_po_line_id(po_id, l_num)
            qty = rng.choice([50, 100, 250, 500, 1000, 2500])
            unit_price = round(rng.uniform(10.0, min(350.0, applied_contract.unit_price_ceiling)), 2)
            line_total = round(qty * unit_price, 2)
            po_total += line_total

            pol = POLine(
                po_line_id=line_id,
                po_id=po_id,
                line_number=l_num,
                item_sku=f"SKU-{sup.category.value[:4].upper()}-{rng.randint(1000, 9999)}",
                description=f"Precision component for {sup.category.value}",
                ordered_qty=qty,
                unit_price=unit_price,
                line_total=line_total,
                required_date=required_date,
                cancelled_qty=0,
                status=POLineStatus.RECEIVED,
            )
            po_lines.append(pol)
            po_lines_for_this_po.append(pol)

        po_created_at = datetime(po_date.year, po_date.month, po_date.day, 9, rng.randint(0, 59))
        po = PurchaseOrder(
            po_id=po_id,
            supplier_id=sup_id,
            contract_id=applied_contract.contract_id,
            site_id=fulfilling_site.site_id,
            po_date=po_date,
            required_delivery_date=required_date,
            total_amount=round(po_total, 2),
            currency="USD",
            status=POStatus.FULFILLED,
            buyer_id=rng.choice(BUYERS),
            created_at=po_created_at,
        )
        purchase_orders.append(po)

    # Now generate Shipments linked to POs
    # Each PO has 1 or 2 shipments to reach target_num_shipments
    # Sample POs to fulfill target shipment volume
    po_pool = list(purchase_orders)
    shipment_allocations = [1] * len(po_pool)
    extra_shipments_needed = target_num_shipments - len(po_pool)
    
    if extra_shipments_needed > 0:
        # Distribute extra shipments across POs
        extra_indices = rng.choices(range(len(po_pool)), k=extra_shipments_needed)
        for idx in extra_indices:
            shipment_allocations[idx] += 1

    for po_idx, po in enumerate(po_pool):
        num_shps = shipment_allocations[po_idx]
        sup_id = po.supplier_id
        archetype = supplier_archetypes.get(sup_id, "STABLE")
        
        # Calculate portion of ordered qty per shipment
        po_total_qty = sum(l.ordered_qty for l in po_lines if l.po_id == po.po_id)
        qty_per_shp = max(1, po_total_qty // num_shps)

        for s_idx in range(num_shps):
            shp_id = format_shipment_id(shipment_counter)
            shipment_counter += 1

            mode = rng.choice([TransportMode.ROAD, TransportMode.AIR, TransportMode.OCEAN])
            transit_days = 2 if mode == TransportMode.AIR else (5 if mode == TransportMode.ROAD else 18)

            dispatch_day_offset = rng.randint(5, max(6, (po.required_delivery_date - po.po_date).days - 2))
            dispatch_date = po.po_date + timedelta(days=dispatch_day_offset)
            est_delivery_date = dispatch_date + timedelta(days=transit_days)

            shp = Shipment(
                shipment_id=shp_id,
                po_id=po.po_id,
                supplier_id=sup_id,
                origin_site_id=po.site_id,
                carrier_code=rng.choice(CARRIERS),
                tracking_number=f"TRK{rng.randint(10000000, 99999999)}",
                dispatch_date=dispatch_date,
                estimated_delivery_date=est_delivery_date,
                shipped_qty=qty_per_shp,
                mode=mode,
                status=ShipmentStatus.DELIVERED,
            )
            shipments.append(shp)

            # Generate DeliveryEvents for this shipment
            # Event 1: Pickup
            pickup_dt = datetime(dispatch_date.year, dispatch_date.month, dispatch_date.day, 10, 0)
            delivery_events.append(
                DeliveryEvent(
                    event_id=format_event_id(event_counter),
                    shipment_id=shp_id,
                    event_type=DeliveryEventType.PICKUP,
                    event_timestamp=pickup_dt,
                    location="Origin Dock",
                    status_code=DeliveryStatusCode.ON_TIME,
                    actual_delivered_qty=0,
                    received_by=None,
                    notes="Dispatched from supplier origin facility",
                )
            )
            event_counter += 1

            # Event 2: In Transit Scan
            mid_date = dispatch_date + timedelta(days=max(1, transit_days // 2))
            mid_dt = datetime(mid_date.year, mid_date.month, mid_date.day, 14, 30)
            delivery_events.append(
                DeliveryEvent(
                    event_id=format_event_id(event_counter),
                    shipment_id=shp_id,
                    event_type=DeliveryEventType.IN_TRANSIT_SCAN,
                    event_timestamp=mid_dt,
                    location="Carrier Transit Hub",
                    status_code=DeliveryStatusCode.ON_TIME,
                    actual_delivered_qty=0,
                    received_by=None,
                    notes="In-transit sorting completed",
                )
            )
            event_counter += 1

            # Event 3: Final Delivery (Arrival & Dock-Receipt)
            # Determine if on-time or delayed based on archetype
            if archetype == "DETERIORATING":
                # 50% delayed past PO required delivery date
                is_delayed = rng.random() < 0.50
            elif archetype == "QUALITY_PRONE":
                is_delayed = rng.random() < 0.12
            else:
                is_delayed = rng.random() < 0.05  # 95% on-time for stable

            if is_delayed:
                # Arrives 1 to 10 days after required_date
                deliv_date = po.required_delivery_date + timedelta(days=rng.randint(1, 10))
                status_code = DeliveryStatusCode.DELAYED
            else:
                # Arrives on or before required_date (and after dispatch_date)
                max_lead = max(1, (po.required_delivery_date - dispatch_date).days)
                deliv_days = min(transit_days, max_lead)
                deliv_date = dispatch_date + timedelta(days=deliv_days)
                if deliv_date < dispatch_date:
                    deliv_date = dispatch_date + timedelta(days=1)
                status_code = DeliveryStatusCode.ON_TIME

            deliv_dt = datetime(deliv_date.year, deliv_date.month, deliv_date.day, rng.randint(11, 17), rng.randint(0, 59))
            delivery_events.append(
                DeliveryEvent(
                    event_id=format_event_id(event_counter),
                    shipment_id=shp_id,
                    event_type=DeliveryEventType.DOCK_RECEIPT,
                    event_timestamp=deliv_dt,
                    location="Inbound Distribution Center",
                    status_code=status_code,
                    actual_delivered_qty=qty_per_shp,
                    received_by="Receiving Team Alpha",
                    notes="Signed dock receipt and accepted into staging",
                )
            )
            event_counter += 1

    # Now generate Inspections to fulfill target_num_inspections
    # Link inspections to shipments
    shipment_pool = list(shipments)
    extra_inspections_needed = target_num_inspections - len(shipment_pool)
    insp_allocations = [1] * len(shipment_pool)
    if extra_inspections_needed > 0:
        extra_insp_indices = rng.choices(range(len(shipment_pool)), k=extra_inspections_needed)
        for idx in extra_insp_indices:
            insp_allocations[idx] += 1

    for s_idx, shp in enumerate(shipment_pool):
        num_insps = insp_allocations[s_idx]
        sup_id = shp.supplier_id
        archetype = supplier_archetypes.get(sup_id, "STABLE")

        for _ in range(num_insps):
            insp_id = format_inspection_id(inspection_counter)
            inspection_counter += 1

            sample_size = rng.choice([80, 125, 200, 315])
            
            # Determine defects based on archetype
            if archetype == "QUALITY_PRONE":
                # Elevated defect rate: 1% to 5%
                defect_pct = rng.uniform(0.012, 0.055)
                units_defective = max(1, int(sample_size * defect_pct))
                defect_type = rng.choice([DefectType.DIMENSIONAL, DefectType.FUNCTIONAL, DefectType.COSMETIC])
            else:
                # Stable: 94% zero defects, 6% small defects
                if rng.random() < 0.94:
                    units_defective = 0
                    defect_type = DefectType.NONE
                else:
                    units_defective = rng.randint(1, 2)
                    defect_type = rng.choice([DefectType.COSMETIC, DefectType.PACKAGING])

            units_passed = sample_size - units_defective
            defect_ppm = round((units_defective / sample_size) * 1_000_000, 1)

            if units_defective == 0:
                disposition = InspectionDisposition.ACCEPTED
            elif units_defective <= 2 and archetype != "QUALITY_PRONE":
                disposition = InspectionDisposition.ACCEPTED_ON_DEVIATION
            else:
                disposition = InspectionDisposition.REJECTED if rng.random() < 0.7 else InspectionDisposition.QUARANTINED

            insp_date = shp.estimated_delivery_date + timedelta(days=rng.randint(0, 2))

            insp = Inspection(
                inspection_id=insp_id,
                shipment_id=shp.shipment_id,
                po_id=shp.po_id,
                supplier_id=sup_id,
                inspection_date=insp_date,
                sample_size_inspected=sample_size,
                units_passed=units_passed,
                units_defective=units_defective,
                defect_type=defect_type,
                defect_ppm=defect_ppm,
                disposition=disposition,
                inspector_id=rng.choice(INSPECTORS),
            )
            inspections.append(insp)

    # Generate Invoices (1 invoice per PO)
    for po in purchase_orders:
        inv_id = format_invoice_id(invoice_counter)
        invoice_counter += 1
        sup_id = po.supplier_id
        archetype = supplier_archetypes.get(sup_id, "STABLE")

        inv_date = po.required_delivery_date + timedelta(days=rng.randint(1, 5))
        due_date = inv_date + timedelta(days=30)
        expected_amt = po.total_amount

        # Determine price variance
        # Deteriorating/QualityProne suppliers have higher dispute probability
        has_discrepancy = rng.random() < (0.22 if archetype in ["DETERIORATING", "QUALITY_PRONE"] else 0.04)
        
        if has_discrepancy:
            # Over-billed by 3% to 12%
            variance_factor = rng.uniform(0.03, 0.12)
            invoiced_amt = round(expected_amt * (1.0 + variance_factor), 2)
            payment_status = InvoicePaymentStatus.DISPUTED
            dispute_reason = InvoiceDisputeReason.PRICE_DISCREPANCY
        else:
            invoiced_amt = expected_amt
            payment_status = InvoicePaymentStatus.PAID
            dispute_reason = InvoiceDisputeReason.NONE

        cost_variance_pct = round(((invoiced_amt - expected_amt) / expected_amt) * 100.0, 2)

        inv = Invoice(
            invoice_id=inv_id,
            po_id=po.po_id,
            supplier_id=sup_id,
            invoice_date=inv_date,
            due_date=due_date,
            invoiced_amount=invoiced_amt,
            po_expected_amount=expected_amt,
            cost_variance_pct=cost_variance_pct,
            payment_status=payment_status,
            dispute_reason=dispute_reason,
        )
        invoices.append(inv)

    return purchase_orders, po_lines, shipments, delivery_events, inspections, invoices
