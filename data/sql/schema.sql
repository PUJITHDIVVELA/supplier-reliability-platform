-- Supplier Reliability Scoring Platform
-- Relational DDL Schema with Foreign Keys and Constraints

CREATE TABLE suppliers (
    supplier_id VARCHAR(16) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    tier VARCHAR(16) NOT NULL,
    category VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    country VARCHAR(64) NOT NULL,
    founded_year INTEGER NOT NULL,
    financial_stability_rating VARCHAR(8) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE sites (
    site_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(16) NOT NULL,
    site_name VARCHAR(128) NOT NULL,
    country VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    address VARCHAR(255) NOT NULL,
    facility_type VARCHAR(32) NOT NULL,
    monthly_capacity_units INTEGER NOT NULL,
    utilized_capacity_units INTEGER NOT NULL,
    iso_certified BOOLEAN NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE contracts (
    contract_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(16) NOT NULL,
    contract_type VARCHAR(64) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    agreed_sla_otd_pct REAL NOT NULL,
    agreed_defect_ppm_threshold INTEGER NOT NULL,
    unit_price_ceiling REAL NOT NULL,
    payment_terms VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE purchase_orders (
    po_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(16) NOT NULL,
    contract_id VARCHAR(32) NOT NULL,
    site_id VARCHAR(32) NOT NULL,
    po_date DATE NOT NULL,
    required_delivery_date DATE NOT NULL,
    total_amount REAL NOT NULL,
    currency VARCHAR(8) NOT NULL,
    status VARCHAR(32) NOT NULL,
    buyer_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

CREATE TABLE po_lines (
    po_line_id VARCHAR(48) PRIMARY KEY,
    po_id VARCHAR(32) NOT NULL,
    line_number INTEGER NOT NULL,
    item_sku VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    ordered_qty INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL,
    required_date DATE NOT NULL,
    cancelled_qty INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
);

CREATE TABLE shipments (
    shipment_id VARCHAR(32) PRIMARY KEY,
    po_id VARCHAR(32), -- Nullable for orphan shipment edge case
    supplier_id VARCHAR(16) NOT NULL,
    origin_site_id VARCHAR(32) NOT NULL,
    carrier_code VARCHAR(64) NOT NULL,
    tracking_number VARCHAR(64) NOT NULL,
    dispatch_date DATE NOT NULL,
    estimated_delivery_date DATE NOT NULL,
    shipped_qty INTEGER NOT NULL,
    mode VARCHAR(16) NOT NULL,
    status VARCHAR(32) NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (origin_site_id) REFERENCES sites(site_id)
);

CREATE TABLE delivery_events (
    event_id VARCHAR(32) PRIMARY KEY,
    shipment_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    location VARCHAR(128) NOT NULL,
    status_code VARCHAR(32) NOT NULL,
    actual_delivered_qty INTEGER NOT NULL,
    received_by VARCHAR(64),
    notes TEXT,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE inspections (
    inspection_id VARCHAR(32) PRIMARY KEY,
    shipment_id VARCHAR(32) NOT NULL,
    po_id VARCHAR(32),
    supplier_id VARCHAR(16) NOT NULL,
    inspection_date DATE NOT NULL,
    sample_size_inspected INTEGER NOT NULL,
    units_passed INTEGER NOT NULL,
    units_defective INTEGER NOT NULL,
    defect_type VARCHAR(32) NOT NULL,
    defect_ppm REAL NOT NULL,
    disposition VARCHAR(32) NOT NULL,
    inspector_id VARCHAR(32) NOT NULL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE invoices (
    invoice_id VARCHAR(32) PRIMARY KEY,
    po_id VARCHAR(32) NOT NULL,
    supplier_id VARCHAR(16) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    invoiced_amount REAL NOT NULL,
    po_expected_amount REAL NOT NULL,
    cost_variance_pct REAL NOT NULL,
    payment_status VARCHAR(32) NOT NULL,
    dispute_reason VARCHAR(64) NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE risk_signals (
    signal_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(16) NOT NULL,
    signal_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    confidence_score REAL NOT NULL,
    detected_at TIMESTAMP, -- Nullable in provenance edge case
    source VARCHAR(128),  -- Nullable in provenance edge case
    status VARCHAR(32) NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE supplier_scores (
    score_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(16) NOT NULL,
    score_period_start DATE NOT NULL,
    score_period_end DATE NOT NULL,
    evaluation_timestamp TIMESTAMP NOT NULL,
    delivery_score REAL NOT NULL,
    quality_score REAL NOT NULL,
    cost_score REAL NOT NULL,
    capacity_score REAL NOT NULL,
    compliance_score REAL NOT NULL,
    disruption_penalty REAL NOT NULL,
    composite_reliability_score REAL NOT NULL,
    reliability_tier VARCHAR(16) NOT NULL,
    decision_recommendation VARCHAR(64) NOT NULL,
    explainability_summary TEXT NOT NULL,
    is_future_data_leakage BOOLEAN NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE ground_truth (
    ground_truth_id VARCHAR(16) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    record_id VARCHAR(48) NOT NULL,
    anomaly_category VARCHAR(64) NOT NULL,
    audit_rule_violated VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    expected_action TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
