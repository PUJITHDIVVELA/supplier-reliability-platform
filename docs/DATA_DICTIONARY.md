# Data Dictionary: Supplier Reliability Platform

This data dictionary formally documents all 11 core relational entities and the isolated ground truth anomaly table in the Supplier Reliability Platform, conforming strictly to Step 1 of the specification.

For each field, the specification outlines:
- **Type**: Python / SQL data type
- **Required / Optional**: Nullability constraints
- **Allowed Values / Enums**: Domain restrictions
- **Units**: Physical or monetary units where applicable
- **Uniqueness**: Primary key or unique constraint
- **Validation Rule**: Integrity or business logic invariant

---

## 1. Table: `suppliers`
**Purpose**: Master registry of qualified vendors and manufacturing partners.  
**Cardinality**: 1 Supplier → $N$ Sites, 1 Supplier → $N$ Contracts, 1 Supplier → $N$ Purchase Orders.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `supplier_id` | `VARCHAR(16)` | Required | Pattern: `^SUP-\d{6}$` | None | **Primary Key** | Must follow `SUP-000001` zero-padded format. Immutable. |
| `name` | `VARCHAR(128)` | Required | Free text | None | Non-unique | Valid company name string length $\ge 3$. |
| `tier` | `VARCHAR(16)` | Required | `Tier-1`, `Tier-2`, `Tier-3` | None | Non-unique | Must belong to `SupplierTier` enum. |
| `category` | `VARCHAR(64)` | Required | `Electronics`, `Precision Machining`, `Raw Materials`, `Assemblies`, `Logistics`, `Packaging` | None | Non-unique | Must belong to `SupplierCategory` enum. |
| `status` | `VARCHAR(32)` | Required | `Active`, `Under Review`, `Suspended`, `Disqualified` | None | Non-unique | Lifecycle state transition must follow valid governance flow. |
| `country` | `VARCHAR(64)` | Required | Standard ISO country names (e.g. US, DE, JP) | None | Non-unique | Valid sovereign jurisdiction. |
| `founded_year` | `INTEGER` | Required | $1900 \le \text{year} \le \text{current year}$ | Year | Non-unique | Must not be future year. |
| `financial_stability_rating` | `VARCHAR(8)` | Required | `AAA`, `AA`, `A`, `BBB`, `BB`, `B`, `CCC` | None | Non-unique | Standard credit rating scale. |
| `created_at` | `TIMESTAMP` | Required | ISO 8601 UTC timestamp | UTC | Non-unique | Timestamp $\le$ current system time. |

---

## 2. Table: `sites`
**Purpose**: Manufacturing plants, assembly facilities, and logistics depots operated by suppliers.  
**Cardinality**: $N$ Sites → 1 Supplier; 1 Site → $N$ Shipments / POs.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `site_id` | `VARCHAR(32)` | Required | Pattern: `^SITE-SUP-\d{6}-\d{2}$` | None | **Primary Key** | Must follow `SITE-<supplier-id>-01` format. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `site_name` | `VARCHAR(128)` | Required | Free text | None | Non-unique | Descriptive facility name. |
| `country` | `VARCHAR(64)` | Required | Country name | None | Non-unique | Geographic location. |
| `city` | `VARCHAR(64)` | Required | City name | None | Non-unique | Municipal location. |
| `address` | `VARCHAR(255)` | Required | Postal address | None | Non-unique | Physical street address. |
| `facility_type` | `VARCHAR(32)` | Required | `Manufacturing`, `Assembly`, `Warehouse/Depot` | None | Non-unique | Enum check. |
| `monthly_capacity_units` | `INTEGER` | Required | $> 0$ | Units / Month | Non-unique | Nameplate physical throughput capacity. |
| `utilized_capacity_units` | `INTEGER` | Required | $\ge 0$ | Units / Month | Non-unique | Cannot be negative. |
| `iso_certified` | `BOOLEAN` | Required | `TRUE`, `FALSE` | None | Non-unique | Quality certification flag (ISO 9001/14001). |
| `status` | `VARCHAR(32)` | Required | `Operational`, `Disrupted`, `Maintenance` | None | Non-unique | Active operating status. |
| `created_at` | `TIMESTAMP` | Required | ISO 8601 UTC timestamp | UTC | Non-unique | Facility creation audit date. |

---

## 3. Table: `contracts`
**Purpose**: Commercial agreements establishing SLA targets, price ceilings, and terms.  
**Cardinality**: $N$ Contracts → 1 Supplier; 1 Contract → $N$ Purchase Orders.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `contract_id` | `VARCHAR(32)` | Required | Pattern: `^CTR-\d{4}-\d{6}$` | None | **Primary Key** | Format `CTR-2026-000001`. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `contract_type` | `VARCHAR(64)` | Required | `Master Services Agreement`, `Fixed Price`, `Volume Discount` | None | Non-unique | Enum validation. |
| `start_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must be $\le$ `end_date`. |
| `end_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must be $\ge$ `start_date`. |
| `agreed_sla_otd_pct` | `REAL` | Required | $0.0 \le \text{rate} \le 100.0$ | Percentage (%) | Non-unique | Contractual On-Time Delivery commitment. |
| `agreed_defect_ppm_threshold` | `INTEGER` | Required | $\ge 0$ | PPM | Non-unique | Maximum acceptable incoming defect rate. |
| `unit_price_ceiling` | `REAL` | Required | $> 0.0$ | USD ($) | Non-unique | Max price allowed for PO line items. |
| `payment_terms` | `VARCHAR(32)` | Required | `Net 30`, `Net 45`, `Net 60`, `Net 90` | None | Non-unique | Commercial settlement terms. |
| `status` | `VARCHAR(32)` | Required | `Active`, `Expired`, `Terminated` | None | Non-unique | Contract validity state. |

---

## 4. Table: `purchase_orders`
**Purpose**: Procurement orders specifying required quantities, dates, and destination fulfillment sites.  
**Cardinality**: 1 Purchase Order → $N$ Lines; 1 Purchase Order → $N$ Shipments; 1 Purchase Order → $N$ Invoices.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `po_id` | `VARCHAR(32)` | Required | Pattern: `^PO-\d{4}-\d{6}$` | None | **Primary Key** | Format `PO-2026-000001`. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `contract_id` | `VARCHAR(32)` | Required | Must exist in `contracts.contract_id` | None | Non-unique | **Foreign Key** → `contracts(contract_id)`. |
| `site_id` | `VARCHAR(32)` | Required | Must exist in `sites.site_id` | None | Non-unique | **Foreign Key** → `sites(site_id)`. Must belong to same supplier (unless deliberate anomaly). |
| `po_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Issue date $\le$ `required_delivery_date`. |
| `required_delivery_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Expected delivery dock date $\ge$ `po_date`. |
| `total_amount` | `REAL` | Required | $\ge 0.0$ | USD ($) | Non-unique | Arithmetic reconciliation: must exactly equal $\sum \text{POLine.line\_total}$. |
| `currency` | `VARCHAR(8)` | Required | `USD` | ISO 4217 | Non-unique | Standard ISO 4217 currency. |
| `status` | `VARCHAR(32)` | Required | `Issued`, `Confirmed`, `In Transit`, `Partially Received`, `Fulfilled`, `Cancelled` | None | Non-unique | Lifecycle transition integrity. |
| `buyer_id` | `VARCHAR(64)` | Required | Planner / Buyer identifier | None | Non-unique | Traceability to actor. |
| `created_at` | `TIMESTAMP` | Required | ISO 8601 UTC timestamp | UTC | Non-unique | Audit log creation date. |

---

## 5. Table: `po_lines`
**Purpose**: Discrete SKU line items ordered under a Purchase Order.  
**Cardinality**: $N$ POLines → 1 Purchase Order.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `po_line_id` | `VARCHAR(48)` | Required | Pattern: `^POL-PO-\d{4}-\d{6}-\d{2}$` | None | **Primary Key** | Format `POL-PO-2026-000001-01`. |
| `po_id` | `VARCHAR(32)` | Required | Must exist in `purchase_orders.po_id` | None | Non-unique | **Foreign Key** → `purchase_orders(po_id)`. |
| `line_number` | `INTEGER` | Required | $\ge 1$ | None | Non-unique | 1-indexed sequential line number. |
| `item_sku` | `VARCHAR(64)` | Required | Alphanumeric SKU identifier | None | Non-unique | Standardized item master SKU. |
| `description` | `TEXT` | Required | Component description | None | Non-unique | Free text description. |
| `ordered_qty` | `INTEGER` | Required | $> 0$ | Units | Non-unique | Quantity ordered. |
| `unit_price` | `REAL` | Required | $> 0.0$ | USD ($) | Non-unique | Unit price $\le$ Contract ceiling. |
| `line_total` | `REAL` | Required | $\ge 0.0$ | USD ($) | Non-unique | Derived value: $\text{ordered\_qty} \times \text{unit\_price}$. |
| `required_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must equal parent PO required date. |
| `cancelled_qty` | `INTEGER` | Required | $\ge 0$ | Units | Non-unique | Cannot exceed `ordered_qty`. |
| `status` | `VARCHAR(32)` | Required | `Open`, `Shipped`, `Received`, `Cancelled` | None | Non-unique | Line lifecycle state. |

---

## 6. Table: `shipments`
**Purpose**: Physical freight dispatches fulfill PO line items.  
**Cardinality**: 1 Shipment → $N$ Delivery Events; 1 Shipment → $N$ Inspections.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shipment_id` | `VARCHAR(32)` | Required | Pattern: `^SHP-\d{4}-\d{6}$` | None | **Primary Key** | Format `SHP-2026-000001`. |
| `po_id` | `VARCHAR(32)` | **Optional** | Must exist in `purchase_orders.po_id` | None | Non-unique | **Foreign Key** → `purchase_orders(po_id)`. Nullable strictly in deliberate orphan shipment edge case. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `origin_site_id` | `VARCHAR(32)` | Required | Must exist in `sites.site_id` | None | Non-unique | **Foreign Key** → `sites(site_id)`. Origin dispatch location. |
| `carrier_code` | `VARCHAR(64)` | Required | DHL, FedEx, Maersk, UPS, DB Schenker, Kuehne+Nagel | None | Non-unique | Authorized carrier code. |
| `tracking_number` | `VARCHAR(64)` | Required | Alphanumeric carrier tracking # | None | Non-unique | Bill of Lading / Airway Bill. |
| `dispatch_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must be $\ge$ PO date. |
| `estimated_delivery_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must be $\ge$ `dispatch_date`. |
| `shipped_qty` | `INTEGER` | Required | $\ge 0$ | Units | Non-unique | Total physical units loaded. |
| `mode` | `VARCHAR(16)` | Required | `Air`, `Ocean`, `Road`, `Rail` | None | Non-unique | Transport mode enum. |
| `status` | `VARCHAR(32)` | Required | `Dispatched`, `In Transit`, `Delivered`, `Exception`, `Lost` | None | Non-unique | Shipment state. |

---

## 7. Table: `delivery_events`
**Purpose**: Immutable milestone audit logs generated along transit and delivery.  
**Cardinality**: $N$ Delivery Events → 1 Shipment.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | `VARCHAR(32)` | Required | Pattern: `^EVT-\d{4}-\d{6}$` | None | **Primary Key** | Format `EVT-2026-000001`. |
| `shipment_id` | `VARCHAR(32)` | Required | Must exist in `shipments.shipment_id` | None | Non-unique | **Foreign Key** → `shipments(shipment_id)`. |
| `event_type` | `VARCHAR(32)` | Required | `Pickup`, `Departure`, `In-Transit-Scan`, `Customs-Hold`, `Arrival`, `Dock-Receipt` | None | Non-unique | Standard milestone lifecycle. |
| `event_timestamp` | `TIMESTAMP` | Required | ISO 8601 UTC timestamp | UTC | Non-unique | Must be $\ge$ shipment dispatch date (unless temporal inversion anomaly). |
| `location` | `VARCHAR(128)` | Required | Free text hub/city location | None | Non-unique | Physical location of scan. |
| `status_code` | `VARCHAR(32)` | Required | `ON_TIME`, `DELAYED`, `DAMAGED`, `HELD` | None | Non-unique | Milestone status. |
| `actual_delivered_qty` | `INTEGER` | Required | $\ge 0$ | Units | Non-unique | Recorded quantity received at dock. |
| `received_by` | `VARCHAR(64)` | Optional | Receiving personnel name/ID | None | Non-unique | Sign-off recipient. |
| `notes` | `TEXT` | Optional | Free text notes | None | Non-unique | Exception notes. |

---

## 8. Table: `inspections`
**Purpose**: Incoming Quality Control (IQC) inspection results and defect metrics.  
**Cardinality**: $N$ Inspections → 1 Shipment.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `inspection_id` | `VARCHAR(32)` | Required | Pattern: `^INS-\d{4}-\d{6}$` | None | **Primary Key** | Format `INS-2026-000001`. |
| `shipment_id` | `VARCHAR(32)` | Required | Must exist in `shipments.shipment_id` | None | Non-unique | **Foreign Key** → `shipments(shipment_id)`. |
| `po_id` | `VARCHAR(32)` | Optional | References `purchase_orders.po_id` | None | Non-unique | **Foreign Key** → `purchase_orders(po_id)`. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `inspection_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must be $\ge$ delivery receipt date. |
| `sample_size_inspected` | `INTEGER` | Required | $> 0$ | Units | Non-unique | ANSI/ASQ standard sample batch size. |
| `units_passed` | `INTEGER` | Required | $\ge 0$ | Units | Non-unique | Arithmetic reconciliation: $\text{passed} + \text{defective} = \text{sample\_size}$. |
| `units_defective` | `INTEGER` | Required | $\ge 0$ | Units | Non-unique | Cannot exceed sample size. |
| `defect_type` | `VARCHAR(32)` | Required | `None`, `Dimensional`, `Cosmetic`, `Functional`, `Packaging` | None | Non-unique | Failure category. |
| `defect_ppm` | `REAL` | Required | $\ge 0.0$ | PPM | Non-unique | Derived value: $(\text{defective} / \text{sample\_size}) \times 1,000,000$. |
| `disposition` | `VARCHAR(32)` | Required | `Accepted`, `Accepted-On-Deviation`, `Rejected`, `Quarantined` | None | Non-unique | Quality control disposition. |
| `inspector_id` | `VARCHAR(32)` | Required | QC Inspector badge identifier | None | Non-unique | Traceability to QA inspector. |

---

## 9. Table: `invoices`
**Purpose**: Commercial supplier invoices reconciled against PO commitments.  
**Cardinality**: $N$ Invoices → 1 Purchase Order.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_id` | `VARCHAR(32)` | Required | Pattern: `^INV-\d{4}-\d{6}$` | None | **Primary Key** | Format `INV-2026-000001`. |
| `po_id` | `VARCHAR(32)` | Required | Must exist in `purchase_orders.po_id` | None | Non-unique | **Foreign Key** → `purchase_orders(po_id)`. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `invoice_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Invoice date $\ge$ PO date. |
| `due_date` | `DATE` | Required | Valid calendar date | Date | Non-unique | Must be $\ge$ `invoice_date`. |
| `invoiced_amount` | `REAL` | Required | $\ge 0.0$ | USD ($) | Non-unique | Total billed amount. |
| `po_expected_amount` | `REAL` | Required | $\ge 0.0$ | USD ($) | Non-unique | Target amount contracted in PO. |
| `cost_variance_pct` | `REAL` | Required | Any real number | % | Non-unique | Derived value: $((\text{invoiced} - \text{expected}) / \text{expected}) \times 100$. |
| `payment_status` | `VARCHAR(32)` | Required | `Pending`, `Approved`, `Disputed`, `Paid` | None | Non-unique | Accounts payable status. |
| `dispute_reason` | `VARCHAR(64)` | Required | `None`, `Price Discrepancy`, `Quantity Mismatch`, `Early Invoice` | None | Non-unique | Reason for AP hold. |

---

## 10. Table: `risk_signals`
**Purpose**: External and internal telemetry signals impacting supplier resilience.  
**Cardinality**: $N$ Risk Signals → 1 Supplier.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `signal_id` | `VARCHAR(32)` | Required | Pattern: `^RSK-SUP-\d{6}-\d{4}-\d{2}$` | None | **Primary Key** | Format `RSK-<supplier-id>-2026-01`. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `signal_type` | `VARCHAR(64)` | Required | `Geopolitical`, `Natural Disaster`, `Financial Distress`, `Cyber Breach`, `Labor Strike`, `Regulatory Non-Compliance` | None | Non-unique | Risk taxonomy category. |
| `severity` | `VARCHAR(16)` | Required | `Low`, `Medium`, `High`, `Critical` | None | Non-unique | Impact severity level. |
| `confidence_score` | `REAL` | Required | $0.0 \le \text{confidence} \le 1.0$ | Ratio | Non-unique | Model / intelligence confidence rating. |
| `detected_at` | `TIMESTAMP` | **Optional** | ISO 8601 UTC timestamp | UTC | Non-unique | Event detection time. Nullable strictly in deliberate provenance edge case. |
| `source` | `VARCHAR(128)` | **Optional** | E.g. Reuters, Dun & Bradstreet, NOAA | None | Non-unique | Originating intelligence provider. Nullable in provenance edge case. |
| `status` | `VARCHAR(32)` | Required | `Active`, `Mitigated`, `False Alarm` | None | Non-unique | Status flag. |

---

## 11. Table: `supplier_scores`
**Purpose**: Multi-signal composite reliability scorecard with explainable sub-scores.  
**Cardinality**: $N$ Scores → 1 Supplier (over time).

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `score_id` | `VARCHAR(32)` | Required | Pattern: `^SCORE-\d{4}-\d{6}$` | None | **Primary Key** | Format `SCORE-2026-000001`. |
| `supplier_id` | `VARCHAR(16)` | Required | Must exist in `suppliers.supplier_id` | None | Non-unique | **Foreign Key** → `suppliers(supplier_id)`. |
| `score_period_start` | `DATE` | Required | Calendar date | Date | Non-unique | Evaluation window start. |
| `score_period_end` | `DATE` | Required | Calendar date | Date | Non-unique | Evaluation window end $\ge$ `start_date`. |
| `evaluation_timestamp` | `TIMESTAMP` | Required | ISO 8601 UTC timestamp | UTC | Non-unique | Must be $\ge$ all incorporated transaction dates (unless future data leakage anomaly). |
| `delivery_score` | `REAL` | Required | $0.0 \le \text{score} \le 100.0$ | Score [0-100] | Non-unique | Clear denominator: Delivered Shipments. |
| `quality_score` | `REAL` | Required | $0.0 \le \text{score} \le 100.0$ | Score [0-100] | Non-unique | Clear denominator: Total Sample Units Inspected. |
| `cost_score` | `REAL` | Required | $0.0 \le \text{score} \le 100.0$ | Score [0-100] | Non-unique | Clear denominator: Total Contract Expected Spend. |
| `capacity_score` | `REAL` | Required | $0.0 \le \text{score} \le 100.0$ | Score [0-100] | Non-unique | Clear denominator: Total Monthly Site Capacity. |
| `compliance_score` | `REAL` | Required | $0.0 \le \text{score} \le 100.0$ | Score [0-100] | Non-unique | SLA, ISO 9001/14001, ESG governance. |
| `disruption_penalty` | `REAL` | Required | $0.0 \le \text{penalty} \le 100.0$ | Deduction | Non-unique | Active severity risk deduction. |
| `composite_reliability_score` | `REAL` | Required | $0.0 \le \text{composite} \le 100.0$ | Score [0-100] | Non-unique | Reconciled: $\sum (W_k \times S_k)$ with $\sum W_k = 1.0$. |
| `reliability_tier` | `VARCHAR(16)` | Required | `Tier-A`, `Tier-B`, `Tier-C`, `Tier-D`, `Tier-F` | None | Non-unique | Deterministic tier thresholds: A($\ge 90$), B($\ge 80$), C($\ge 70$), D($\ge 60$), F($<60$). |
| `decision_recommendation` | `VARCHAR(64)` | Required | `Preferred Partner`, `Maintain Allocation`, `Active Monitoring`, `Conditional Review`, `Disqualify / Exit` | None | Non-unique | Mapped directly from Tier. |
| `explainability_summary` | `TEXT` (JSON) | Required | Valid JSON object | None | Non-unique | Full mathematical telemetry breakdown. |
| `is_future_data_leakage` | `BOOLEAN` | Required | `TRUE`, `FALSE` | None | Non-unique | Temporal lookahead audit flag. |

---

## 12. Table: `ground_truth` (Isolated)
**Purpose**: Independent ground truth registry of all injected anomalies and expected validation decisions. Never leaked into operational scoring features.

| Field Name | Type | Required / Optional | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ground_truth_id` | `VARCHAR(16)` | Required | Pattern: `^GT-\d{6}$` | None | **Primary Key** | Format `GT-000001`. |
| `entity_type` | `VARCHAR(32)` | Required | Table name (`Shipment`, `DeliveryEvent`, `SupplierScore`, `RiskSignal`, `PurchaseOrder`) | None | Non-unique | Target entity table. |
| `record_id` | `VARCHAR(48)` | Required | Primary key of target record | None | Unique | Target record identifier. |
| `anomaly_category` | `VARCHAR(64)` | Required | `ORPHAN_SHIPMENT`, `TEMPORAL_INVERSION`, `FUTURE_DATA_LEAKAGE`, `MISSING_PROVENANCE`, `CONFLATED_SITE` | None | Non-unique | Official anomaly category. |
| `audit_rule_violated` | `VARCHAR(64)` | Required | Rule code | None | Non-unique | Specific audit invariant broken. |
| `severity` | `VARCHAR(16)` | Required | `Critical`, `High`, `Medium` | None | Non-unique | Operational risk level. |
| `expected_action` | `TEXT` | Required | Free text recommendation | None | Non-unique | Prescribed analyst/system action. |
| `description` | `TEXT` | Required | Free text explanation | None | Non-unique | Audit finding description. |
| `created_at` | `TIMESTAMP` | Required | ISO 8601 UTC timestamp | UTC | Non-unique | Label timestamp. |
