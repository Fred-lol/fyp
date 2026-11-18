import sys
from collections import Counter
from psycopg.errors import DeadlockDetected
from pathlib import Path

from components.charts import capacity_chart, bar_chart, render_chart, BLUE
import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import staff_sidebar, require_staff
from components.display import friendly_datetime
from services.optimization_service import get_plan, list_plans, saved_weight_utilization
from services.report_service import generate_report, list_reports, get_report, report_csv_bytes

bootstrap_app()

st.set_page_config(page_title="Reports & Analytics | AquaLoad", page_icon="📊", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
page_header(
    "Loading Reports & Analytics",
    "Review loading plans saved in the past 30 days and compare lorry capacity use.",
    "Operational Insight",
)

@st.cache_data(ttl=300, show_spinner=False)
def plan_box_counts(plan_id):
    plan = get_plan(plan_id)
    return Counter(p["box_name"] for p in plan["placements"]) if plan else Counter()


def render_reports(plans):
    st.header("Generate Loading Report", anchor=False)
    if not plans:
        st.info("No loading plans were saved in the past 30 days.")
    else:
        plan_map = {
            f"Plan #{p['plan_id']} · {p['plate_number']} · {p.get('collection_point') or 'No collection point'}": p
            for p in plans
        }
        plan_label = st.selectbox("Saved Loading Plan", list(plan_map))
        selected_plan = plan_map[plan_label]
        if st.button("Generate Report", type="primary"):
            ok, msg, report_id = generate_report(selected_plan["plan_id"], st.session_state.user_id)
            (st.success if ok else st.error)(msg)
            if ok:
                st.session_state.selected_report_id = report_id

    current_ids = {plan["plan_id"] for plan in plans}
    reports = [report for report in list_reports() if report["plan_id"] in current_ids]
    if reports:
        st.header("Recent Loading Reports", anchor=False)
        report_search = st.text_input("Find a report", placeholder="Lorry or collection point")
        reports = [r for r in reports if report_search.casefold() in f"{r['plate_number']} {r.get('collection_point') or ''}".casefold()]
        if not reports:
            st.info("No reports match your search.")
            return
        report_rows = [{
            "Report": f"#{r['report_id']}",
            "Loading Plan": f"#{r['plan_id']}",
            "Lorry": r["plate_number"],
            "Collection Point": r.get("collection_point") or "Not assigned",
            "Generated On": friendly_datetime(r["generated_at"]),
            "Boxes": r["total_boxes"],
            "Space Used": f"{float(r['space_utilization']):.1f}%",
            "Loaded Weight": f"{float(r['total_weight']):,.1f} kg",
            "Validation": r["validation_result"],
        } for r in reports]
        st.dataframe(pd.DataFrame(report_rows), width="stretch", hide_index=True)

        report_ids = [r["report_id"] for r in reports]
        default_report = st.session_state.get("selected_report_id")
        if default_report not in report_ids:
            default_report = report_ids[0]
        report_id = st.selectbox(
            "View Report",
            report_ids,
            index=report_ids.index(default_report),
            format_func=lambda rid: f"Report #{rid}",
        )
        report = get_report(report_id)
        if not report:
            st.info("This report is no longer in the current 30-day view.")
            return
        plan = report["plan"]

        st.divider()
        st.header(f"Loading Report #{report_id}", anchor=False)
        st.caption(
            f"Plan #{plan['plan_id']} · {plan['plate_number']} · {plan.get('collection_point') or 'No collection point'} · Generated {friendly_datetime(report['generated_at'])}"
        )

        a, b, c, d = st.columns(4)
        a.metric("Lorry Volume Used", f"{float(plan['space_utilization']):.1f}%", f"{report['unused_space_percent']:.1f}% remains")
        b.metric("Total Boxes", int(plan["total_boxes"]))
        c.metric("Loaded Weight", f"{float(plan['total_weight']):,.1f} kg")
        d.metric("Plan Status", "✓ Valid" if plan["validation_result"] == "Valid" else plan["validation_result"])

        st.subheader("Capacity Use", anchor=False)
        render_chart(capacity_chart([dict(plan, weight_utilization=report["weight_usage_percent"])]), "report_capacity")

        st.info(report["operational_insight"])

        left, right = st.columns(2, gap="large")
        with left:
            st.subheader("Orders Included", anchor=False)
            orders_df = pd.DataFrame([{
                "Order": f"#{o['order_id']}",
                "Customer": o["customer_name"],
                "Seafood Weight": f"{float(o['seafood_weight_kg']):,.1f} kg",
            } for o in plan["orders"]])
            st.dataframe(orders_df, width="stretch", hide_index=True)

        with right:
            st.subheader("Box Size Breakdown", anchor=False)
            box_df = pd.DataFrame([
                {"Box Template": name, "Quantity": qty}
                for name, qty in report["box_breakdown"].items()
            ])
            if not box_df.empty:
                st.dataframe(box_df, width="stretch", hide_index=True)
                render_chart(bar_chart(box_df["Box Template"], box_df["Quantity"], "Boxes used", horizontal=True, counts=True), "report_boxes")


        st.subheader("Validation", anchor=False)
        for check in report["validation_checks"]:
            st.write(f"✓ {check}")

        csv_bytes = report_csv_bytes(report_id, report=report)
        st.download_button(
            "Download Loading Report (CSV)",
            data=csv_bytes,
            file_name=f"AquaLoad_Loading_Report_{report_id}.csv",
            mime="text/csv",
            width="stretch",
        )
    else:
        st.info("There are no reports for plans saved in the past 30 days.")

def render_analytics(plans):
    st.header("Loading Performance Overview", anchor=False)
    rows = [plan for plan in reversed(plans) if plan["validation_result"] == "Valid"]
    if not rows:
        st.info("There are no valid loading plans from the past 30 days.")
        return

    df = pd.DataFrame(rows)
    df["weight_utilization"] = [saved_weight_utilization(plan) for plan in rows]
    df["collection_point"] = df["collection_point"].fillna("Not assigned")
    df["total_weight"] = df["total_weight"].astype(float)
    df["space_utilization"] = df["space_utilization"].astype(float)

    plans_col, volume_col, weight_col, boxes_col = st.columns(4)
    plans_col.metric("Loading plans", len(df))
    volume_col.metric("Average volume used", f"{df.space_utilization.mean():.1f}%")
    weight_col.metric("Average weight used", f"{df.weight_utilization.mean():.1f}%")
    boxes_col.metric("Boxes loaded", int(df.total_boxes.sum()))
    lorry, loaded, low = st.columns(3)
    lorry.metric("Most-used lorry", df.plate_number.mode().iloc[0])
    loaded.metric("Total loaded weight (kg)", f"{df.total_weight.sum():,.1f}")
    low.metric("Plans below 40% space use", int((df.space_utilization < 40).sum()))

    st.subheader("Space Utilization by Loading Plan", anchor=False)
    st.caption("Volume and weight are separate capacity checks for the same saved plan.")
    render_chart(capacity_chart(df.to_dict("records")), "analytics_capacity")
    if ((df.space_utilization > 100) | (df.weight_utilization > 100)).any():
        st.warning("A saved plan exceeds 100% capacity. Review its loading data before use.")
    st.subheader("Loaded Weight by Plan", anchor=False)
    render_chart(bar_chart([f"Plan #{p}" for p in df.plan_id], df.total_weight.tolist(), "Loaded weight (kg)", color=BLUE), "analytics_weight")
    left, right = st.columns(2)
    with left:
        st.subheader("Box Size Usage", anchor=False)
        counts = Counter()
        for plan_id in df.plan_id:
            counts.update(plan_box_counts(int(plan_id)))
        if counts:
            render_chart(bar_chart(list(counts), list(counts.values()), "Boxes used", horizontal=True, counts=True), "analytics_boxes")
        else:
            st.info("No box-placement history is available.")
    with right:
        st.subheader("Lorry Usage", anchor=False)
        counts = df.groupby("plate_number").size()
        render_chart(bar_chart(counts.index.tolist(), counts.tolist(), "Loading plans", counts=True, color=BLUE), "analytics_lorries")
    st.subheader("Collection Point Usage", anchor=False)
    counts = df.groupby("collection_point").size().sort_values(ascending=False)
    render_chart(bar_chart(counts.index.tolist(), counts.tolist(), "Loading plans", horizontal=True, counts=True), "analytics_points")


report_tab, analytics_tab = st.tabs(["Loading Reports", "Analytics"], on_change="rerun")
try:
    plans = list_plans()
    if report_tab.open:
        with report_tab:
            render_reports(plans)
    if analytics_tab.open:
        with analytics_tab:
            render_analytics(plans)
except DeadlockDetected:
    st.warning("Loading records are temporarily busy. Try again in a moment.")
    st.button("Retry")
