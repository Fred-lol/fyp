import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import staff_sidebar, require_staff
from services.optimization_service import list_plans
from services.report_service import generate_report, list_reports, get_report, report_csv_bytes
from services.analytics_service import (
    analytics_summary,
    utilization_series,
    plans_by_lorry,
    box_usage,
    plans_by_collection_point,
)

bootstrap_app()

def friendly_datetime(value):
    try:
        return pd.to_datetime(value).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(value)


def aqua_chart(chart):
    """Apply accessible AquaLoad chart styling in light and dark appearances."""
    dark = st.session_state.get("theme_preference") == "dark"
    text = "#f5fbfd" if dark else "#123b57"
    muted = "#bfd0d9" if dark else "#617b8d"
    grid = "#315363" if dark else "#d7e6ec"
    return chart.configure_view(stroke=None).configure_axis(
        labelColor=text, titleColor=text, domainColor=grid, tickColor=grid,
        gridColor=grid, labelFontSize=12, titleFontSize=12,
    ).configure_legend(labelColor=text, titleColor=text).configure_title(
        color=text, fontSize=16, fontWeight=700, anchor="start"
    ).configure_range(
        category=["#00aeb7", "#087ab0", "#d8a441", "#df7055"]
    )

st.set_page_config(page_title="Reports & Analytics | AquaLoad", page_icon="📊", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
page_header(
    "Loading Reports & Analytics",
    "Understand what happened in each saved loading plan and compare useful loading performance across operations.",
    "Operational Insight",
)

report_tab, analytics_tab = st.tabs(["Loading Reports", "Analytics"])

with report_tab:
    st.header("Generate Loading Report", anchor=False)
    plans = list_plans()
    if not plans:
        st.info("No saved loading plans are available yet.")
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

    reports = list_reports()
    if reports:
        st.header("Recent Loading Reports", anchor=False)
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
        st.dataframe(pd.DataFrame(report_rows), use_container_width=True, hide_index=True)

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
        plan = report["plan"]

        st.divider()
        st.header(f"Loading Report #{report_id}", anchor=False)
        st.caption(
            f"Plan #{plan['plan_id']} · {plan['plate_number']} · {plan.get('collection_point') or 'No collection point'} · Generated {friendly_datetime(report['generated_at'])}"
        )

        a, b, c, d = st.columns(4)
        a.metric("Space Used", f"{float(plan['space_utilization']):.1f}%", f"{report['unused_space_percent']:.1f}% remains")
        b.metric("Total Boxes", int(plan["total_boxes"]))
        c.metric("Loaded Weight", f"{float(plan['total_weight']):,.1f} kg")
        d.metric("Plan Status", "✓ Valid" if plan["validation_result"] == "Valid" else plan["validation_result"])

        st.subheader("Capacity Use", anchor=False)
        st.progress(
            min(max(float(plan["space_utilization"]) / 100.0, 0.0), 1.0),
            text=f"Lorry volume used: {float(plan['space_utilization']):.1f}% · Remaining: {report['unused_space_percent']:.1f}%",
        )
        st.progress(
            min(max(report["weight_usage_percent"] / 100.0, 0.0), 1.0),
            text=f"Weight capacity used: {report['weight_usage_percent']:.1f}% · Remaining: {float(plan['remaining_weight_capacity']):,.1f} kg",
        )

        st.info(report["operational_insight"])

        left, right = st.columns(2, gap="large")
        with left:
            st.subheader("Orders Included", anchor=False)
            orders_df = pd.DataFrame([{
                "Order": f"#{o['order_id']}",
                "Customer": o["customer_name"],
                "Seafood Weight": f"{float(o['seafood_weight_kg']):,.1f} kg",
            } for o in plan["orders"]])
            st.dataframe(orders_df, use_container_width=True, hide_index=True)

        with right:
            st.subheader("Box Size Breakdown", anchor=False)
            box_df = pd.DataFrame([
                {"Box Template": name, "Quantity": qty}
                for name, qty in report["box_breakdown"].items()
            ])
            if not box_df.empty:
                st.dataframe(box_df, use_container_width=True, hide_index=True)
                chart_df = box_df.set_index("Box Template")[["Quantity"]]
                st.bar_chart(chart_df)

        st.subheader("Validation", anchor=False)
        for check in report["validation_checks"]:
            st.write(f"✓ {check}")

        csv_bytes = report_csv_bytes(report_id)
        st.download_button(
            "Download Loading Report (CSV)",
            data=csv_bytes,
            file_name=f"AquaLoad_Loading_Report_{report_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("No loading reports have been generated yet.")

with analytics_tab:
    summary = analytics_summary()
    st.header("Loading Performance Overview", anchor=False)
    a, b, c, d, e = st.columns(5)
    a.metric("Loading Plans", summary["total_plans"])
    b.metric("Average Space Used", f"{summary['avg_utilization']:.1f}%")
    c.metric("Average Weight Used", f"{summary['avg_weight_utilization']:.1f}%")
    d.metric("Best Space Used", f"{summary['max_utilization']:.1f}%")
    e.metric("Boxes Loaded", summary["total_boxes"])
    st.info(
        f"Most-used lorry: {summary['most_used_lorry']} | Total loaded weight: {summary['total_weight']:,.1f} kg | "
        f"Plans below 40% space use: {summary['low_utilization_plans']}"
    )
    st.caption(f"Most frequently used lorry: {summary['most_used_lorry']} · Total loaded weight recorded: {summary['total_weight']:,.1f} kg")

    series = utilization_series()
    if not series:
        st.info("Analytics will appear after valid loading plans are saved.")
    else:
        df = pd.DataFrame(series)
        st.subheader("Space Utilization by Loading Plan", anchor=False)
        util_df = df[["plan_id", "space_utilization"]].copy()
        util_df["Loading Plan"] = util_df["plan_id"].map(lambda x: f"Plan #{x}")
        capacity_df = df.melt(
            id_vars=["plan_id", "plate_number", "collection_point"],
            value_vars=["space_utilization", "weight_utilization"],
            var_name="Capacity Type", value_name="Percent Used",
        )
        capacity_df["Loading Plan"] = capacity_df["plan_id"].map(lambda value: f"Plan #{value}")
        capacity_df["Capacity Type"] = capacity_df["Capacity Type"].map({
            "space_utilization": "Lorry volume", "weight_utilization": "Weight capacity",
        })
        capacity_chart = alt.Chart(capacity_df).mark_bar(size=420, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Loading Plan:N", title="Loading plan", sort=None, scale=alt.Scale(paddingInner=0.12, paddingOuter=0.06)),
            xOffset=alt.XOffset("Capacity Type:N", sort=["Lorry volume", "Weight capacity"], scale=alt.Scale(paddingInner=0, paddingOuter=0)),
            y=alt.Y("Percent Used:Q", title="Capacity used (%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Capacity Type:N", title=None),
            tooltip=["Loading Plan:N", "plate_number:N", "collection_point:N", "Capacity Type:N", alt.Tooltip("Percent Used:Q", format=".1f")],
        ).properties(height=310)
        st.altair_chart(aqua_chart(capacity_chart), use_container_width=True)

        st.subheader("Loaded Weight by Plan", anchor=False)
        weight_df = df[["plan_id", "total_weight"]].copy()
        weight_df["Loading Plan"] = weight_df["plan_id"].map(lambda x: f"Plan #{x}")
        weight_chart = alt.Chart(weight_df).mark_bar(color="#087ab0", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Loading Plan:N", title="Loading plan", sort=None),
            y=alt.Y("total_weight:Q", title="Loaded seafood weight (kg)"),
            tooltip=["Loading Plan:N", alt.Tooltip("total_weight:Q", title="Loaded weight (kg)", format=",.1f")],
        ).properties(height=300)
        st.altair_chart(aqua_chart(weight_chart), use_container_width=True)

        left, right = st.columns(2, gap="large")
        with left:
            st.subheader("Box Size Usage", anchor=False)
            boxes = pd.DataFrame(box_usage())
            if not boxes.empty:
                box_chart = alt.Chart(boxes).mark_bar(color="#00aeb7", cornerRadiusEnd=5).encode(
                    y=alt.Y("box_name:N", title=None, sort="-x"),
                    x=alt.X("quantity:Q", title="Boxes used", axis=alt.Axis(format="d", tickMinStep=1)),
                    tooltip=[alt.Tooltip("box_name:N", title="Box template"), alt.Tooltip("quantity:Q", title="Boxes used", format=".0f")],
                ).properties(height=max(180, 48 * len(boxes)))
                st.altair_chart(aqua_chart(box_chart), use_container_width=True)
            else:
                st.info("No box-placement history is available.")

        with right:
            st.subheader("Lorry Usage", anchor=False)
            lorries = pd.DataFrame(plans_by_lorry())
            if not lorries.empty:
                lorry_chart = alt.Chart(lorries).mark_bar(color="#d8a441", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X("plate_number:N", title="Lorry", sort="-y"),
                    y=alt.Y("plan_count:Q", title="Saved loading plans", axis=alt.Axis(format="d", tickMinStep=1)),
                    tooltip=["plate_number:N", alt.Tooltip("plan_count:Q", title="Plans", format=".0f"), alt.Tooltip("avg_utilization:Q", title="Average space used (%)", format=".1f"), alt.Tooltip("avg_weight_utilization:Q", title="Average weight used (%)", format=".1f"), alt.Tooltip("total_weight:Q", title="Total loaded kg", format=",.1f")],
                ).properties(height=max(180, 48 * len(lorries)))
                st.altair_chart(aqua_chart(lorry_chart), use_container_width=True)

        st.subheader("Collection Point Usage", anchor=False)
        points = pd.DataFrame(plans_by_collection_point())
        if not points.empty:
            point_chart = alt.Chart(points).mark_bar(color="#df7055", cornerRadiusEnd=5).encode(
                y=alt.Y("collection_point:N", title=None, sort="-x"),
                x=alt.X("plan_count:Q", title="Saved loading plans", axis=alt.Axis(format="d", tickMinStep=1)),
                tooltip=["collection_point:N", alt.Tooltip("plan_count:Q", title="Plans", format=".0f"), alt.Tooltip("avg_utilization:Q", title="Average space used (%)", format=".1f"), alt.Tooltip("total_weight:Q", title="Total loaded kg", format=",.1f")],
            ).properties(height=max(180, 48 * len(points)))
            st.altair_chart(aqua_chart(point_chart), use_container_width=True)
            st.dataframe(
                points.rename(columns={
                    "collection_point": "Collection Point",
                    "plan_count": "Loading Plans",
                    "avg_utilization": "Average Space Used (%)",
                }),
                use_container_width=True,
                hide_index=True,
            )
