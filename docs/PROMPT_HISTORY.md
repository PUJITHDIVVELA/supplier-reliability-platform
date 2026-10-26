# Prompt History & Interaction Log

**Candidate Project**: Supplier Reliability Platform  
**Recruitment Drive**: YottaFlex AI  
**Date**: October 2026

In compliance with YottaFlex Guideline 03 (*"Submit your prompt history and explain where AI accelerated your work, where you relied heavily on it, and what you personally reviewed, changed, or validated"*), the record below summarizes the sequential engineering prompts, design inquiries, and iterative instructions used during development.

---

## Prompt 1: Requirements Ingestion & Scope Definition
> **Prompt**:  
> "Analyze the YottaFlex problem statement: 'Score supplier reliability using delivery, quality, cost, capacity, compliance and disruption signals.' Break down the 11 required entities (Supplier, Site, Contract, PurchaseOrder, POLine, Shipment, DeliveryEvent, Inspection, Invoice, RiskSignal, SupplierScore), the 5 mandatory edge cases (orphan shipment, temporal inversion, future data leakage, missing provenance, conflated sites), and the 10-step synthetic generation instructions. Outline the architecture to ensure non-leakage of ground truth labels."
>
> **Outcome & Human Review**:  
> Designed the decoupled architecture where operational tables remain clean and free of classification flags, and an isolated `ground_truth.json` records true anomalies. Formulated mathematical equations for all 6 scoring pillars.

---

## Prompt 2: Relational Data Dictionary & Schema Modeling
> **Prompt**:  
> "Generate a data dictionary and Pydantic models for all 11 entities conforming to the nomenclature conventions: SUP-000001; SITE-<supplier-id>-01; PO-2026-000001; SHP-2026-000001; RSK-<supplier-id>-2026-01; SCORE-2026-000001. Ensure primary keys, foreign keys, cardinality (1:1, 1:N, N:M), allowed enums, and validation invariants are explicitly specified."
>
> **Outcome & Human Review**:  
> Refined field bounds, made `po_id` on `Shipment` optional to represent the orphan shipment edge case, and ensured `RiskSignal.detected_at` and `source` were optional for provenance edge cases.

---

## Prompt 3: Transactional Data Generation with Realistic Archetypes
> **Prompt**:  
> "Build the data generator enforcing realistic distributions: stable performers (70%), deteriorating lead times (15%), quality incidents (10%), and low-volume / cold-start suppliers (5%). Ensure all derived values (line totals, PO totals, defect PPM, invoice variance) reconcile arithmetically from source records rather than being generated independently. Support parameterized scale: micro, starter, and full (1,000 suppliers, 10,000 POs, 15,000 shipments, 20,000 inspections)."
>
> **Outcome & Human Review**:  
> Reviewed lead time distributions and arrival date logic to ensure valid date ordering, and validated that PO total amounts match the sum of child PO line items.

---

## Prompt 4: Multi-Signal Scoring Engine with Explainability
> **Prompt**:  
> "Implement the 6-pillar scoring formula (Delivery, Quality, Cost, Capacity, Compliance, Disruption) with clear denominators. Explicitly handle missing data for suppliers with no delivery or inspection history. Generate a structured explainability JSON payload containing raw metrics, subscores, and top positive/negative drag drivers."
>
> **Outcome & Human Review**:  
> Validated weight sum ($25\% + 25\% + 15\% + 15\% + 10\% + 10\% = 100\%$), bounded all component scores to $[0.0, 100.0]$, and mapped score intervals to Tiers (A, B, C, D, F) and recommendations.

---

## Prompt 5: Audit Engine & Ground Truth Benchmarking
> **Prompt**:  
> "Develop an AuditEngine that evaluates the 7 integrity checks (PK uniqueness, FK integrity, allowed enums, date ordering, arithmetic reconciliation, site tenancy conflation, and risk provenance). Benchmark detected issues against ground_truth.json to output true positives, false positives, false negatives, precision, recall, and F1-score."
>
> **Outcome & Human Review**:  
> Tested on full baseline dataset (1,000 suppliers, 10k POs, 15k shipments, 20k inspections) and verified 100% precision, 100% recall, and 1.0000 F1-score across all 70 injected anomalies.

---

## Prompt 6: Interactive Dashboard & CLI
> **Prompt**:  
> "Create a Rich CLI with commands (generate, validate, reproduce, explain, dashboard) and an interactive 5-tab Streamlit dashboard (Executive Portfolio, Supplier 360° Radar, Relational Traceability, Anomaly Center, What-If Simulator)."
>
> **Outcome & Human Review**:  
> Tested CLI locally, confirmed fixed-seed reproducibility across independent runs, and verified that all Streamlit tabs render cleanly with responsive Plotly charts.
