# 🛡️ Supplier Reliability & Resilience Platform
> **Enterprise Multi-Signal Supplier Scoring, Synthetic Data Generation, and Audit Engine**  
> *Built for the YottaFlex AI Recruitment Drive*

![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/pytest-9%20passed-brightgreen.svg)
![Precision / Recall](https://img.shields.io/badge/Audit%20F1--Score-1.0000%20(100%25)-success.svg)
![Reproducibility](https://img.shields.io/badge/Reproducibility-100%25%20Bit--for--Bit-blueviolet.svg)

---

## 📌 Executive Summary
Supply chain resilience requires an objective, quantifiable, and transparent mechanism to score vendor performance. The **Supplier Reliability Platform** is an end-to-end software solution that ingests and evaluates multi-signal telemetry across **Delivery**, **Quality**, **Cost**, **Capacity**, **Compliance**, and **Disruption signals**.

The system exposes operational decisions and exceptions, maintains immutable audit lineage across 11 relational entities, handles cold-start/missing data explicitly with clear denominators, injects 5 realistic edge cases, and verifies integrity through an audit engine benchmarked against an isolated ground truth dataset with **100% precision and recall**.

---

## 🏗️ Architecture & Core Entities

The platform models 11 core entities connected via strict primary and foreign keys:

```
[Supplier] (1) <---> (N) [Site]
    │ (1)
    ├────────> (N) [Contract]
    │ (1)
    ├────────> (N) [PurchaseOrder] (1) <---> (N) [POLine]
    │ (1)             │ (1)
    │                 ├────────> (N) [Shipment] (1) <---> (N) [DeliveryEvent]
    │                 │ (1)             │ (1)
    │                 │                 └────────> (N) [Inspection]
    │                 └────────> (N) [Invoice]
    │ (1)
    ├────────> (N) [RiskSignal]
    │ (1)
    └────────> (N) [SupplierScore]
```

### Deterministic ID Nomenclature Conventions
- **Supplier**: `SUP-000001` (6 digits zero-padded)
- **Site**: `SITE-<supplier-id>-01` (e.g., `SITE-SUP-000001-01`)
- **Contract**: `CTR-2026-000001`
- **Purchase Order**: `PO-2026-000001`
- **PO Line Item**: `POL-PO-2026-000001-01`
- **Shipment**: `SHP-2026-000001`
- **Delivery Event**: `EVT-2026-000001`
- **Quality Inspection**: `INS-2026-000001`
- **Invoice**: `INV-2026-000001`
- **Disruption Risk Signal**: `RSK-<supplier-id>-2026-01`
- **Supplier Scorecard**: `SCORE-2026-000001`
- **Ground Truth Record**: `GT-000001`

---

## 📐 Explainable Scoring Formula (6 Pillars)

Every sub-score is bounded $[0.00, 100.00]$ with an **explicit mathematical denominator**:

| Pillar | Weight ($W_k$) | Denominator | Core Metric | Missing Data Handling |
| :--- | :---: | :--- | :--- | :--- |
| **Delivery Reliability** | `25%` | Total delivered shipments ($N_{\text{deliv}}$) | $70\% \times \text{OTD Rate} + 30\% \times \text{Fill Rate}$ | Defaults to $75.0$; flags `insufficient_delivery_data=True` |
| **Quality Performance** | `25%` | Total sample units inspected ($U_{\text{inspected}}$) | $\text{Accept Rate} \times 100 - \text{PPM Penalty}$ | Defaults to $80.0$; flags `insufficient_quality_data=True` |
| **Cost & Invoicing** | `15%` | Total PO expected spend ($\text{Spend}_{\text{expected}}$) | $100 - (\text{Variance} \times 150 + \text{Disputes} \times 25)$ | Defaults to $85.0$; flags `insufficient_cost_data=True` |
| **Capacity Stability** | `15%` | Total monthly nameplate capacity ($C_{\text{total}}$) | Utilization within $55\%-85\%$ ideal band | Penalizes bottleneck overload or subscale viability |
| **Compliance & Governance** | `10%` | Active facilities & contracts | Deductions for missing ISO 9001/14001 or expired contracts | Base 100 minus compliance deductions |
| **Disruption Risk** | `10%` | Active telemetry events | Deduction based on severity (Critical: -30, High: -16, Med: -6) | Multiplied by intelligence confidence score |

**Composite Score**:
$$S_{\text{composite}} = \sum_{k} W_k \times S_k \quad (\text{Bounded } [0.0, 100.0])$$

### Tiers & Recommendations
- **Tier-A ($90 - 100$)**: Preferred Partner (Eligible for auto-replenishment & multi-year master contracts)
- **Tier-B ($80 - 89.9$)**: Maintain Allocation (Satisfactory standard vendor)
- **Tier-C ($70 - 79.9$)**: Active Monitoring (Corrective action plan required; bi-weekly reviews)
- **Tier-D ($60 - 69.9$)**: Conditional Review (Freeze on new product lines; executive audit)
- **Tier-F ($< 60$)**: Disqualify / Exit (Immediate volume redirection to secondary sources)

---

## 🚨 Mandated Edge Cases & Ground Truth Non-Leakage

To strictly prevent data leakage into input features, operational tables (`shipments`, `purchase_orders`, `delivery_events`, `supplier_scores`, `risk_signals`) **do not contain any anomaly classification column**.

Deliberate edge cases are recorded in an isolated `ground_truth.json` / `ground_truth.csv` file:

1. **Shipment has no PO (`ORPHAN_SHIPMENT`)**: Physical shipment dispatched with `po_id = NULL`.
2. **Delivery date precedes dispatch (`DELIVERY_BEFORE_DISPATCH`)**: Delivery dock-receipt event timestamp occurs chronologically prior to shipment dispatch date.
3. **Supplier score uses future data (`TIMESTAMP_LEAKAGE`)**: Supplier score calculated at historical timestamp $T_{\text{eval}}$ incorporates future transactions dated $T > T_{\text{eval}}$ (look-ahead bias).
4. **Risk signal has no source/time (`NULL_PROVENANCE`)**: External disruption alert missing source accreditation and detection timestamp.
5. **Supplier sites are conflated (`SITE_TENANCY_MISMATCH`)**: Purchase order fulfilled by a site belonging to a foreign supplier.

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.9+ (Python 3.10 recommended)
- Git

### 2. Setup
```bash
git clone <your-repository-url>
cd supplier-reliability-platform
python3 -m pip install -e .
```

### 3. Generate Synthetic Dataset
Generate baseline dataset across all 11 tables + ground truth:
```bash
# Starter scale (100 suppliers, 1,000 POs, 1,500 shipments, 2,000 inspections)
python3 -m supplier_reliability.cli generate --scale starter --seed 20261022

# Full baseline scale (1,000 suppliers, 10,000 POs, 15,000 shipments, 20,000 inspections)
python3 -m supplier_reliability.cli generate --scale full --seed 20261022
```

Outputs generated in:
- `data/csv/*.csv` (11 tables + isolated `ground_truth.csv`)
- `data/json/*.json`
- `data/sqlite/supplier_reliability.db`
- `data/sql/schema.sql`
- `data/manifest.json` (Includes cryptographic SHA-256 hashes and row counts)

### 4. Run Audit & Validation Suite
Audit all 7 integrity and business rules and benchmark against ground truth:
```bash
python3 -m supplier_reliability.cli validate --scale starter
# Or full enterprise scale:
python3 -m supplier_reliability.cli validate --scale full
```

### 5. Verify 100% Bit-for-Bit Reproducibility (Step 10)
Regenerate twice independently with the same seed and compare row counts and SHA-256 hashes:
```bash
python3 -m supplier_reliability.cli reproduce --seed 20261022 --scale starter
```

### 6. Inspect Individual Supplier Scorecard Decomposition
Inspect the 6-pillar breakdown, telemetry denominators, and primary/secondary drag drivers:
```bash
python3 -m supplier_reliability.cli explain SUP-000001
```

### 7. Launch Interactive Web Dashboard
Launch the 5-tab Streamlit application:
```bash
streamlit run supplier_reliability/web/app.py
# Or via CLI:
python3 -m supplier_reliability.cli dashboard
```
Open your browser at `http://localhost:8501`.

### 8. Run Automated Pytest Suite
```bash
pytest -v
```

---

## 📊 Interactive Web Application Tour

The Streamlit web application includes 5 comprehensive views:
1. **Executive Portfolio Dashboard**: High-level KPIs, portfolio tier distribution pie charts, boxplots of scores across categories, top strategic partners, and highest disruption risk vendors.
2. **Supplier 360° Radar Scorecard**: Interactive 6-pillar radar chart comparing vendor performance against industry benchmarks, detailed metric cards with explicit denominators, and driver diagnostics.
3. **End-to-End Relational Traceability**: Trace any PO to its line items, carrier shipments, transit scan milestones, incoming QC defect PPM, and invoice payment settlements.
4. **Exception & Audit Center**: Live ledger of detected violations across all 5 edge case categories, with live confusion matrix metrics (Precision: 100%, Recall: 100%, F1: 1.0000).
5. **What-If Policy Simulator**: Dynamic sliders to adjust pillar weights (auto-normalized to 100%), simulating real-time portfolio score re-ranking and tier shifts.

---

## 📚 Complete Project Documentation

- 📖 [**Data Dictionary**](file:///Users/abhi/.gemini/antigravity-ide/scratch/supplier-reliability-platform/docs/DATA_DICTIONARY.md): Complete field-by-field dictionary for all 11 entities + ground truth (types, constraints, enums, units, validation rules).
- 🏛️ [**Architecture & Design**](file:///Users/abhi/.gemini/antigravity-ide/scratch/supplier-reliability-platform/docs/ARCHITECTURE.md): Mathematical formulations, actor workflows, entity relationship diagram, and tradeoffs.
- 🧪 [**Validation Summary**](file:///Users/abhi/.gemini/antigravity-ide/scratch/supplier-reliability-platform/docs/VALIDATION_SUMMARY.md): Empirical audit results and ground truth benchmark performance.
- 🔄 [**Reproducibility Report**](file:///Users/abhi/.gemini/antigravity-ide/scratch/supplier-reliability-platform/docs/REPRODUCIBILITY.md): Cryptographic SHA-256 hash matrices proving bit-for-bit reproducibility.
- 🤖 [**AI Transparency Disclosure**](file:///Users/abhi/.gemini/antigravity-ide/scratch/supplier-reliability-platform/docs/AI_TRANSPARENCY.md): Disclosure of AI acceleration, human review, and architectural decisions.
- 📝 [**Prompt History**](file:///Users/abhi/.gemini/antigravity-ide/scratch/supplier-reliability-platform/docs/PROMPT_HISTORY.md): Complete log of prompts and engineering iterations conforming to YottaFlex recruitment guidelines.

---

## ⚖️ Lawful Provenance & Public Data Guidance
All data generated by this platform is 100% synthetic, created deterministically using mathematical and probabilistic rules without any confidential, proprietary, or personal identifiable information (PII). Public reference data was utilized solely for domain inspiration (e.g. standard country names, ISO standards, and manufacturing terminology) under lawful, permissive open use.

---

**Developed for YottaFlex AI Candidate Project**  
*Evaluation Window: 72 Hours • Individual Work • Transparent AI Use*
