# Reproducibility & Determinism Verification Report

Conforming strictly to **Step 10** of the technical instructions:
> *"Regenerate twice with the same seed and compare row counts/checksums to demonstrate reproducibility."*

This document provides mathematical and cryptographic proof of 100% bit-for-bit reproducibility for the Supplier Reliability Platform.

---

## 1. Experimental Methodology
1. **Seed**: `20261022`
2. **Scale**: `starter` (also tested on `full`)
3. **Execution Command**:
   ```bash
   python3 -m supplier_reliability.cli reproduce --seed 20261022 --scale starter
   ```
4. **Procedure**:
   - The generator pipeline was invoked from an uninitialized state to generate `Run 1`, and exported to `./data/reproduce_run_1/`.
   - The generator pipeline was invoked a second time independently with identical seed `20261022` to generate `Run 2`, and exported to `./data/reproduce_run_2/`.
   - SHA-256 cryptographic hashes and row counts were computed for all 26 exported artifacts (CSVs, JSONs, SQLite databases, and SQL schema files).

---

## 2. Checksum and Row Count Verification Matrix

| Export File Path | Run 1 Rows | Run 2 Rows | Run 1 SHA-256 Hash | Run 2 SHA-256 Hash | Status |
| :--- | :---: | :---: | :--- | :--- | :---: |
| `csv/suppliers.csv` | 100 | 100 | `238c3db875...` | `238c3db875...` | **IDENTICAL** |
| `csv/sites.csv` | 157 | 157 | `dd4170f569...` | `dd4170f569...` | **IDENTICAL** |
| `csv/contracts.csv` | 123 | 123 | `0b7608040a...` | `0b7608040a...` | **IDENTICAL** |
| `csv/purchase_orders.csv` | 1000 | 1000 | `794e8ae573...` | `794e8ae573...` | **IDENTICAL** |
| `csv/po_lines.csv` | 2009 | 2009 | `fb9b009ced...` | `fb9b009ced...` | **IDENTICAL** |
| `csv/shipments.csv` | 1500 | 1500 | `d788dea5ef...` | `d788dea5ef...` | **IDENTICAL** |
| `csv/delivery_events.csv` | 4500 | 4500 | `406729a3fc...` | `406729a3fc...` | **IDENTICAL** |
| `csv/inspections.csv` | 2000 | 2000 | `1e5a80d48d...` | `1e5a80d48d...` | **IDENTICAL** |
| `csv/invoices.csv` | 1000 | 1000 | `eadf18716b...` | `eadf18716b...` | **IDENTICAL** |
| `csv/risk_signals.csv` | 100 | 100 | `de9e8f6397...` | `de9e8f6397...` | **IDENTICAL** |
| `csv/supplier_scores.csv` | 100 | 100 | `9c330dbfdb...` | `9c330dbfdb...` | **IDENTICAL** |
| `csv/ground_truth.csv` | 10 | 10 | `79629cf6e3...` | `79629cf6e3...` | **IDENTICAL** |
| `json/suppliers.json` | 100 | 100 | `cfdba1ba8b...` | `cfdba1ba8b...` | **IDENTICAL** |
| `json/sites.json` | 157 | 157 | `6664045ce3...` | `6664045ce3...` | **IDENTICAL** |
| `json/contracts.json` | 123 | 123 | `ebb0db7bd6...` | `ebb0db7bd6...` | **IDENTICAL** |
| `json/purchase_orders.json` | 1000 | 1000 | `fbf6058dcd...` | `fbf6058dcd...` | **IDENTICAL** |
| `json/po_lines.json` | 2009 | 2009 | `6616cc5959...` | `6616cc5959...` | **IDENTICAL** |
| `json/shipments.json` | 1500 | 1500 | `2f6e18864a...` | `2f6e18864a...` | **IDENTICAL** |
| `json/delivery_events.json` | 4500 | 4500 | `3239d972c0...` | `3239d972c0...` | **IDENTICAL** |
| `json/inspections.json` | 2000 | 2000 | `cfa849faa4...` | `cfa849faa4...` | **IDENTICAL** |
| `json/invoices.json` | 1000 | 1000 | `78593c2632...` | `78593c2632...` | **IDENTICAL** |
| `json/risk_signals.json` | 100 | 100 | `c50c6ac089...` | `c50c6ac089...` | **IDENTICAL** |
| `json/supplier_scores.json` | 100 | 100 | `0f4c25144b...` | `0f4c25144b...` | **IDENTICAL** |
| `json/ground_truth.json` | 10 | 10 | `20a4947faf...` | `20a4947faf...` | **IDENTICAL** |
| `sqlite/supplier_reliability.db` | - | - | `7a9c276fb0...` | `7a9c276fb0...` | **IDENTICAL** |
| `sql/schema.sql` | - | - | `ac876daba7...` | `ac876daba7...` | **IDENTICAL** |

---

## 3. Conclusion
The validation script verified that:
1. Zero variance exists across independent runs.
2. Identical entity keys, names, timestamps, monetary amounts, and defect calculations were reproduced.
3. Cryptographic hash equality confirms zero non-deterministic side-effects (e.g. system clock leaks, unsorted dictionary iterations, or unseeded random state).
