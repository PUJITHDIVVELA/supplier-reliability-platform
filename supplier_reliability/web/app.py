"""
Supplier Reliability Platform - Interactive Web Application.
Provides 5 executive & operational modules:
1. Executive Intelligence & Portfolio Reliability Dashboard
2. Supplier 360° Profile & Radar Scorecard Explainer
3. End-to-End Relational Traceability Explorer (PO -> Shipment -> QC -> Invoice)
4. Anomaly & Exception Detection Center (Audit against Ground Truth)
5. Interactive What-If Scenario & Policy Simulation
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.validator.audit_engine import AuditEngine
from supplier_reliability.config import DEFAULT_SEED

st.set_page_config(
    page_title="Supplier Reliability Platform | YottaFlex",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-weight: 600;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def load_data(scale: str, seed: int):
    dataset = run_pipeline(scale=scale, seed=seed, inject_anomalies=True)
    engine = AuditEngine(dataset)
    audit_report = engine.run_all_validations()
    return dataset, audit_report


# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/supplier.png", width=64)
    st.markdown("### **Platform Controls**")
    selected_scale = st.selectbox("Data Scale Profile", ["starter", "micro", "full"], index=0)
    selected_seed = st.number_input("Deterministic Seed", value=DEFAULT_SEED, step=1)

    with st.spinner("Synchronizing synthetic data pipeline..."):
        dataset, audit_report = load_data(selected_scale, selected_seed)

    st.success(f"Pipeline Active: {len(dataset.suppliers)} Suppliers, {len(dataset.purchase_orders)} POs, {len(dataset.shipments)} Shipments")
    st.divider()
    st.markdown("**Core Actors Supported:**")
    st.markdown("• Supplier (Self-Service Profile)\n• Planner (PO & Capacity Allocation)\n• Logistics Analyst (Carrier Milestones)\n• Quality Inspector (Incoming QC PPM)\n• Operations Director (Tier Allocation)")


# Header Banner
st.markdown('<div class="main-header">🛡️ Supplier Reliability & Resilience Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-signal supplier reliability scoring with delivery, quality, cost, capacity, compliance, and disruption telemetry.</div>', unsafe_allow_html=True)

# Create Main Tabs
tab_exec, tab_profile, tab_trace, tab_anomalies, tab_simulator = st.tabs([
    "📊 Executive Portfolio",
    "🎯 Supplier 360° Scorecard",
    "🔗 Relational Traceability",
    "🚨 Exception & Audit Center",
    "🎛️ What-If Policy Simulator"
])

# -------------------------------------------------------------
# TAB 1: EXECUTIVE PORTFOLIO
# -------------------------------------------------------------
with tab_exec:
    scores_df = pd.DataFrame([s.model_dump() for s in dataset.supplier_scores])
    suppliers_df = pd.DataFrame([s.model_dump() for s in dataset.suppliers])
    merged_df = scores_df.merge(suppliers_df, on="supplier_id")

    # High Level KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Suppliers", len(suppliers_df))
    with col2:
        avg_score = round(scores_df["composite_reliability_score"].mean(), 1)
        st.metric("Avg Portfolio Score", f"{avg_score} / 100")
    with col3:
        preferred_count = sum(scores_df["reliability_tier"] == "Tier-A")
        st.metric("Tier-A Partners", preferred_count, f"{preferred_count/len(scores_df)*100:.1f}%")
    with col4:
        at_risk_count = sum(scores_df["reliability_tier"].isin(["Tier-D", "Tier-F"]))
        st.metric("At-Risk Suppliers", at_risk_count, delta=f"-{at_risk_count}", delta_color="inverse")
    with col5:
        total_pos = len(dataset.purchase_orders)
        st.metric("Active POs Tracked", total_pos)

    st.markdown("---")

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Reliability Tier Distribution")
        tier_counts = scores_df["reliability_tier"].value_counts().reset_index()
        tier_counts.columns = ["Tier", "Count"]
        color_map = {
            "Tier-A": "#10B981",
            "Tier-B": "#3B82F6",
            "Tier-C": "#F59E0B",
            "Tier-D": "#EF4444",
            "Tier-F": "#991B1B",
        }
        fig_tier = px.pie(
            tier_counts,
            names="Tier",
            values="Count",
            color="Tier",
            color_discrete_map=color_map,
            hole=0.45,
        )
        fig_tier.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_tier, use_container_width=True)

    with c2:
        st.subheader("Composite Score by Category")
        fig_cat = px.box(
            merged_df,
            x="category",
            y="composite_reliability_score",
            color="category",
            points="all",
        )
        fig_cat.update_layout(showlegend=False, xaxis_title="", yaxis_title="Reliability Score (0-100)")
        st.plotly_chart(fig_cat, use_container_width=True)

    st.subheader("Top Strategic Suppliers vs Highest Disruption Risk")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Top 5 Preferred Partners (Tier-A)**")
        top_5 = merged_df.sort_values(by="composite_reliability_score", ascending=False).head(5)
        st.dataframe(
            top_5[["supplier_id", "name", "category", "composite_reliability_score", "delivery_score", "quality_score"]],
            hide_index=True,
            use_container_width=True
        )
    with c4:
        st.markdown("**Top 5 At-Risk Suppliers Requiring Immediate Mitigation**")
        bottom_5 = merged_df.sort_values(by="composite_reliability_score", ascending=True).head(5)
        st.dataframe(
            bottom_5[["supplier_id", "name", "category", "composite_reliability_score", "disruption_penalty", "reliability_tier"]],
            hide_index=True,
            use_container_width=True
        )

# -------------------------------------------------------------
# TAB 2: SUPPLIER 360° SCORECARD & EXPLAINER
# -------------------------------------------------------------
with tab_profile:
    st.subheader("🎯 Individual Supplier Deep-Dive & Multi-Signal Explainer")
    supplier_options = {s.supplier_id: f"{s.supplier_id} - {s.name} ({s.category.value})" for s in dataset.suppliers}
    selected_sup_id = st.selectbox("Select Supplier to Audit", list(supplier_options.keys()), format_func=lambda x: supplier_options[x])

    selected_sup = next(s for s in dataset.suppliers if s.supplier_id == selected_sup_id)
    selected_score = next(sc for sc in dataset.supplier_scores if sc.supplier_id == selected_sup_id)
    exp = selected_score.explainability_summary

    # Overview header
    sup_col1, sup_col2, sup_col3, sup_col4 = st.columns([2, 1, 1, 1])
    with sup_col1:
        st.markdown(f"### **{selected_sup.name}**")
        st.caption(f"ID: `{selected_sup.supplier_id}` | Country: {selected_sup.country} | Founded: {selected_sup.founded_year} | Category: {selected_sup.category.value}")
    with sup_col2:
        st.metric("Composite Score", f"{selected_score.composite_reliability_score:.1f} / 100")
    with sup_col3:
        st.metric("Reliability Tier", selected_score.reliability_tier.value)
    with sup_col4:
        st.metric("Decision", selected_score.decision_recommendation.value)

    st.divider()

    # Radar Chart & Explanatory Breakdown
    col_radar, col_metrics = st.columns([1, 1])
    with col_radar:
        st.markdown("#### **6-Pillar Radar Fingerprint**")
        categories = ['Delivery (25%)', 'Quality (25%)', 'Cost (15%)', 'Capacity (15%)', 'Compliance (10%)', 'Disruption (10%)']
        values = [
            selected_score.delivery_score,
            selected_score.quality_score,
            selected_score.cost_score,
            selected_score.capacity_score,
            selected_score.compliance_score,
            max(0.0, 100.0 - selected_score.disruption_penalty)
        ]
        values.append(values[0])
        categories.append(categories[0])

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=selected_sup.name,
            line=dict(color='#3B82F6', width=2),
            fillcolor='rgba(59, 130, 246, 0.25)'
        ))
        # Benchmark line (avg of all suppliers)
        benchmark_vals = [
            scores_df["delivery_score"].mean(),
            scores_df["quality_score"].mean(),
            scores_df["cost_score"].mean(),
            scores_df["capacity_score"].mean(),
            scores_df["compliance_score"].mean(),
            (100.0 - scores_df["disruption_penalty"]).mean(),
        ]
        benchmark_vals.append(benchmark_vals[0])
        fig_radar.add_trace(go.Scatterpolar(
            r=benchmark_vals,
            theta=categories,
            name='Portfolio Benchmark',
            line=dict(color='#94A3B8', dash='dash')
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            margin=dict(t=20, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_metrics:
        st.markdown("#### **Explainable Telemetry & Denominators**")
        raw = exp.get("raw_metrics", {})
        drivers = exp.get("top_drivers", {})

        st.markdown(f"""
        - **🚚 On-Time Delivery Rate**: `{raw.get('on_time_rate_pct', 0)}%` (Delivered: `{raw.get('on_time_shipments', 0)}` on-time out of `{raw.get('total_delivered_shipments', 0)}` total delivered shipments)
        - **🔬 Quality Defect PPM**: `{raw.get('defect_ppm', 0):,.1f} PPM` (Passed: `{raw.get('accept_rate_pct', 0)}%` across `{raw.get('total_inspected_units', 0):,}` sample units)
        - **💰 Spend & Price Variance**: `{raw.get('spend_variance_pct', 0)}%` invoice discrepancy vs PO contract ceiling
        - **🏭 Committed Capacity**: `{raw.get('capacity_utilization_pct', 0)}%` monthly utilization across active facilities
        - **⚠️ Active Disruption Signals**: `{raw.get('active_risk_signal_count', 0)}` active events (Penalty: `-{raw.get('disruption_penalty_points', 0)} pts`)
        """)

        st.info(f"**Key Driver Insights:**\n"
                f"• **Primary Drag:** `{drivers.get('primary_drag', ('-', 0))[0]}` ({drivers.get('primary_drag', ('-', 0))[1]:.1f}/100)\n"
                f"• **Secondary Drag:** `{drivers.get('secondary_drag', ('-', 0))[0]}` ({drivers.get('secondary_drag', ('-', 0))[1]:.1f}/100)\n"
                f"• **Strongest Asset:** `{drivers.get('strongest_pillar', ('-', 0))[0]}` ({drivers.get('strongest_pillar', ('-', 0))[1]:.1f}/100)")

# -------------------------------------------------------------
# TAB 3: RELATIONAL TRACEABILITY
# -------------------------------------------------------------
with tab_trace:
    st.subheader("🔗 End-to-End Lineage & Audit Trail")
    st.markdown("Trace full lifecycle from **Supplier Master** → **Fulfilling Site** → **Purchase Order** → **Shipment** → **Carrier Delivery** → **Incoming QC** → **Invoice Reconciliation**.")

    po_options = [p.po_id for p in dataset.purchase_orders[:200]]
    selected_po_id = st.selectbox("Select Purchase Order to Trace", po_options)

    po = next(p for p in dataset.purchase_orders if p.po_id == selected_po_id)
    po_lines = [l for l in dataset.po_lines if l.po_id == selected_po_id]
    shps = [s for s in dataset.shipments if s.po_id == selected_po_id]
    invs = [inv for inv in dataset.invoices if inv.po_id == selected_po_id]

    col_po, col_shp, col_qc = st.columns(3)
    with col_po:
        st.markdown(f"#### 📄 Purchase Order: `{po.po_id}`")
        st.write(f"• **Supplier ID:** `{po.supplier_id}`\n• **Site ID:** `{po.site_id}`\n• **PO Date:** `{po.po_date}`\n• **Required Delivery:** `{po.required_delivery_date}`\n• **Total Amount:** `${po.total_amount:,.2f}`\n• **Status:** `{po.status.value}`")
        st.markdown("**PO Line Items:**")
        st.dataframe(pd.DataFrame([l.model_dump() for l in po_lines])[["line_number", "item_sku", "ordered_qty", "unit_price", "line_total"]], hide_index=True)

    with col_shp:
        st.markdown(f"#### 📦 Linked Shipments ({len(shps)})")
        if shps:
            for s in shps:
                st.write(f"• **Shipment ID:** `{s.shipment_id}`\n• **Carrier:** `{s.carrier_code}`\n• **Tracking:** `{s.tracking_number}`\n• **Dispatch Date:** `{s.dispatch_date}`\n• **Shipped Qty:** `{s.shipped_qty}` units\n• **Mode:** `{s.mode.value}`")
                events = [e for e in dataset.delivery_events if e.shipment_id == s.shipment_id]
                st.caption(f"Carrier Milestone Events ({len(events)} logged):")
                st.dataframe(pd.DataFrame([e.model_dump() for e in events])[["event_type", "event_timestamp", "location", "status_code"]], hide_index=True)
        else:
            st.warning("No shipment found linked to this PO.")

    with col_qc:
        st.markdown("#### 🔬 Incoming Quality & Invoicing")
        insps = [i for i in dataset.inspections if i.po_id == selected_po_id]
        if insps:
            for i in insps:
                st.write(f"• **Inspection ID:** `{i.inspection_id}`\n• **Sample Size:** `{i.sample_size_inspected}` units\n• **Defects:** `{i.units_defective}` ({i.defect_ppm:,.1f} PPM)\n• **Disposition:** `{i.disposition.value}`")
        else:
            st.info("No incoming QC record logged.")

        st.markdown("**Invoice Settlement:**")
        if invs:
            for inv in invs:
                st.write(f"• **Invoice ID:** `{inv.invoice_id}`\n• **Billed:** `${inv.invoiced_amount:,.2f}`\n• **Variance:** `{inv.cost_variance_pct:.2f}%`\n• **Status:** `{inv.payment_status.value}`")
        else:
            st.info("Invoice pending.")

# -------------------------------------------------------------
# TAB 4: EXCEPTION & AUDIT CENTER
# -------------------------------------------------------------
with tab_anomalies:
    st.subheader("🚨 Exception & Anomaly Detection Center")
    st.markdown("Evaluates all 7 integrity and business rules against the isolated ground truth dataset.")

    eval_data = audit_report.ground_truth_evaluation

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Ground Truth Injected", eval_data.get("total_ground_truth_anomalies", 0))
    with kpi2:
        st.metric("Audit Detected Violations", eval_data.get("total_detected_anomalies", 0))
    with kpi3:
        st.metric("Detection Precision", f"{eval_data.get('precision', 0.0) * 100:.1f}%")
    with kpi4:
        st.metric("Detection Recall", f"{eval_data.get('recall', 0.0) * 100:.1f}%")

    st.divider()

    st.markdown("#### **Evaluation by Anomaly Category**")
    cat_df = pd.DataFrame(eval_data.get("category_breakdown", {})).T.reset_index()
    if not cat_df.empty:
        cat_df.columns = ["Anomaly Category", "Ground Truth Count", "Detected Count"]
        st.dataframe(cat_df, hide_index=True, use_container_width=True)

    st.markdown("#### **Live Audit Violation Ledger**")
    issues_df = pd.DataFrame([
        {
            "Rule Code": issue.rule_code,
            "Entity": issue.entity_type,
            "Record ID": issue.record_id,
            "Severity": issue.severity,
            "Audit Message": issue.message,
        }
        for issue in audit_report.issues
    ])
    st.dataframe(issues_df, hide_index=True, use_container_width=True)

# -------------------------------------------------------------
# TAB 5: WHAT-IF POLICY SIMULATOR
# -------------------------------------------------------------
with tab_simulator:
    st.subheader("🎛️ Interactive Reliability Policy & Weight Simulator")
    st.markdown("Adjust scoring pillar weights and evaluate real-time re-ranking and tier redistribution across the entire supplier base.")

    c_w1, c_w2, c_w3 = st.columns(3)
    with c_w1:
        w_del = st.slider("Delivery Weight (%)", 0, 50, 25, 5)
        w_qual = st.slider("Quality Weight (%)", 0, 50, 25, 5)
    with c_w2:
        w_cost = st.slider("Cost Accuracy Weight (%)", 0, 50, 15, 5)
        w_cap = st.slider("Capacity Weight (%)", 0, 50, 15, 5)
    with c_w3:
        w_comp = st.slider("Compliance Weight (%)", 0, 30, 10, 5)
        w_dis = st.slider("Disruption Weight (%)", 0, 30, 10, 5)

    total_w = w_del + w_qual + w_cost + w_cap + w_comp + w_dis
    if total_w != 100:
        st.warning(f"Total weights sum to **{total_w}%** (Normalizing dynamically to 100%).")
        norm_factor = 100.0 / total_w
    else:
        norm_factor = 1.0

    sim_weights = {
        "delivery": (w_del * norm_factor) / 100.0,
        "quality": (w_qual * norm_factor) / 100.0,
        "cost": (w_cost * norm_factor) / 100.0,
        "capacity": (w_cap * norm_factor) / 100.0,
        "compliance": (w_comp * norm_factor) / 100.0,
        "disruption": (w_dis * norm_factor) / 100.0,
    }

    # Recalculate scores with sim_weights
    sim_scores = []
    for sc in dataset.supplier_scores:
        re_comp = (
            sim_weights["delivery"] * sc.delivery_score +
            sim_weights["quality"] * sc.quality_score +
            sim_weights["cost"] * sc.cost_score +
            sim_weights["capacity"] * sc.capacity_score +
            sim_weights["compliance"] * sc.compliance_score +
            sim_weights["disruption"] * (100.0 - sc.disruption_penalty)
        )
        re_comp = round(max(0.0, min(100.0, re_comp)), 2)
        new_tier = "Tier-A" if re_comp >= 90.0 else ("Tier-B" if re_comp >= 80.0 else ("Tier-C" if re_comp >= 70.0 else ("Tier-D" if re_comp >= 60.0 else "Tier-F")))
        sim_scores.append({
            "supplier_id": sc.supplier_id,
            "original_score": sc.composite_reliability_score,
            "simulated_score": re_comp,
            "score_delta": round(re_comp - sc.composite_reliability_score, 2),
            "original_tier": sc.reliability_tier.value,
            "simulated_tier": new_tier,
        })

    sim_df = pd.DataFrame(sim_scores)
    st.markdown("#### **Policy Impact: Tier Redistribution**")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Original Tier Counts**")
        st.write(sim_df["original_tier"].value_counts().to_dict())
    with col_t2:
        st.markdown("**Simulated Tier Counts**")
        st.write(sim_df["simulated_tier"].value_counts().to_dict())

    st.markdown("#### **Supplier Score Re-Ranking Table**")
    st.dataframe(sim_df.sort_values(by="simulated_score", ascending=False), hide_index=True, use_container_width=True)
