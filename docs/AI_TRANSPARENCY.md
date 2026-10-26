# AI Transparency & Human-AI Collaboration Disclosure

**Organization**: YottaFlex AI Recruitment Drive  
**Project**: Supplier Reliability Scoring Platform  
**Guideline Compliance**: Section 03 ("USE LLMs TRANSPARENTLY") & Section 04 ("MAKE YOUR REASONING VISIBLE")

---

## 1. Executive Summary of AI Use
In accordance with YottaFlex guidelines, this document discloses how AI tools were utilized during the development of the Supplier Reliability Platform. AI was utilized as an **accelerator for boilerplate generation, exploratory synthesis, and multi-file code structuring**, while all **business architecture, mathematical formulations, audit invariants, edge case logic, and verification suites were critically designed, reviewed, and validated**.

---

## 2. Where AI Accelerated the Work
1. **Boilerplate Pydantic & Relational Modeling**:
   - Accelerating the initial transcription of 11 relational entities into Pydantic models with field constraints.
2. **Deterministic Name and Location Dictionaries**:
   - Compiling lists of realistic manufacturing company prefixes, suffixes, global cities, and logistics carriers.
3. **Streamlit UI Layout & Plotly Visualizations**:
   - Drafting Plotly polar radar charts and metric card HTML/CSS templates.

---

## 3. Where Heavy Reliance Occurred & Required Human Intervention
1. **Data Non-Leakage Architecture**:
   - *Initial AI bias*: AI models frequently attempt to add an `is_anomaly` or `anomaly_type` column directly onto the transaction table (e.g., adding `anomaly_type` to `Shipment` or `PurchaseOrder`).
   - *Human Correction*: We strictly enforced the separation of operational tables and ground truth. Operational tables remain purely functional and standard, while anomaly classifications reside solely in `ground_truth.json` / `ground_truth.csv`. The `AuditEngine` detects violations strictly via deterministic business rules without knowing the ground truth labels in advance.
2. **Mathematical Denominator Precision**:
   - *AI draft*: Attempted to use generic counts without handling zero-volume suppliers or edge conditions.
   - *Human Design*: Defined exact, mathematically sound denominators for all 6 pillars (delivered shipments for OTD, inspected units for PPM, expected spend for invoice variance, nameplate capacity for utilization) with explicit neutral baselines (e.g. 75.0, 80.0) and data sufficiency flags (`insufficient_delivery_data = True`).
3. **Temporal Inversion & Historical Snapshot Integrity**:
   - Ensured that `SupplierScore` respects temporal point-in-time snapshots to prevent lookahead bias (Edge Case 3), where future events are excluded from historical evaluation runs.

---

## 4. Key Architectural Decisions & Trade-Offs

### Decision 1: Relational Architecture vs Flattened Table
- *Trade-off*: A single flattened denormalized table is simpler to generate, but fails to model real-world supply chain reality where 1 supplier operates multiple manufacturing sites, fulfills multiple POs across contracts, and splits freight into multiple carrier shipments.
- *Choice*: Modeled full 11 relational entities with primary/foreign keys, enabling realistic many-to-one and one-to-many joins.

### Decision 2: Archetype-Based Generation vs Uniform Random Sampling
- *Trade-off*: Pure uniform random sampling produces unrealistic homogeneous supplier behavior.
- *Choice*: Implemented 4 distinct supplier archetypes:
  - **Stable Performers (70%)**: High OTD ($\ge 95\%$), defect PPM $< 500$, minimal invoice variance.
  - **Deteriorating Lead Time (15%)**: Lengthening lead times, frequent carrier delays ($40-60\%$ delayed), elevated capacity utilization ($> 88\%$).
  - **Quality-Prone (10%)**: Elevated defect rates ($15,000-60,000$ PPM), rejected lots, higher dispute rates.
  - **Low-Volume / Cold-Start (5%)**: Very few or zero POs, testing explicit missing data handling.

### Decision 3: Deterministic Pseudo-Random Generator (Fixed Seed)
- *Trade-off*: Non-deterministic systems cannot be audited or replicated across different environments.
- *Choice*: Fixed seed `20261022` with independent scoped `random.Random(seed)` instances ensures 100% bit-for-bit reproducibility and identical SHA-256 hashes across independent runs.

---

## 5. Limitations & Future Work
1. **Streaming Telemetry**: Current engine operates on batch evaluation snapshots; future enhancements could integrate Apache Kafka / Flink for sub-second event-driven stream scoring.
2. **Machine Learning Predictive Scoring**: While the current engine uses explainable deterministic business formulas, combining it with an XGBoost / LightGBM model for failure prediction would offer predictive as well as historical reliability metrics.
