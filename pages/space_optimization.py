import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.cards import info_card
from components.theme import apply_theme, page_header
from components.tables import render_dataframe, render_data_editor
from components.navigation import staff_sidebar, require_staff
from components.feedback import flash
from services.collection_point_service import list_lorry_delivery_collection_points
from services.lorry_service import is_valid_lorry_configuration, list_lorries
from services.order_service import eligible_orders_for_optimization
from services.optimization_service import (
    preview_optimization,
    save_optimization,
    get_requirements_for_orders,
)


def _placement_signature(plan):
    """Stable representation used to tell a new plan from the current one."""
    return tuple(sorted(
        (
            int(placement["order_id"]),
            int(placement.get("box_profile_id") or 0),
            int(placement["box_instance"]),
            round(float(placement["x"]), 6), round(float(placement["y"]), 6), round(float(placement["z"]), 6),
            round(float(placement["placed_length"]), 6), round(float(placement["placed_width"]), 6), round(float(placement["placed_height"]), 6),
            str(placement.get("orientation") or ""),
        )
        for placement in plan.get("placements", [])
    ))

bootstrap_app()
st.set_page_config(page_title="Space Optimization | AquaLoad", page_icon="⚙️", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
page_header(
    "3D Space Optimization",
    "Generate a valid compact arrangement for Ready for Loading orders going to the same collection point.",
    "Core Optimization",
)

points = list_lorry_delivery_collection_points("Available")
if not points:
    st.error("No lorry-delivery collection points are currently available.")
    st.stop()

st.markdown("## Step 1 — Select Collection Point")
point_map = {f"{p['point_name']} · {p['city']}, {p['state']}": p for p in points}
point_label = st.selectbox("Collection Point", list(point_map))
point = point_map[point_label]

st.divider()
st.markdown("## Step 2 — Select Lorry")
lorries = sorted(
    (lorry for lorry in list_lorries("Available") if is_valid_lorry_configuration(lorry)),
    key=lambda item: (float(item["max_weight"]), item["plate_number"]),
)
if not lorries:
    st.error("No available lorry profile has valid Malaysian cargo dimensions for optimization.")
    st.stop()
lorry_map = {
    f"{l['plate_number']} · {l['internal_length']:g}×{l['internal_width']:g}×{l['internal_height']:g} cm · {l['max_weight']:g} kg": l
    for l in lorries
}
# On the first visit all eligible orders are selected by default. Preselect the
# smallest available lorry that can carry their combined box weight; Staff can
# still deliberately choose another lorry and will receive the capacity check.
initial_orders = eligible_orders_for_optimization(point["collection_point_id"])
initial_weight = sum(float(order["estimated_weight"] or 0) for order in initial_orders)
initial_recommended = next(
    (item for item in lorries if float(item["max_weight"]) + 1e-9 >= initial_weight),
    None,
)
initial_recommended_label = next(
    (label for label, item in lorry_map.items() if initial_recommended and item["lorry_id"] == initial_recommended["lorry_id"]),
    None,
)
# Existing sessions may still hold a label for a legacy lorry that no longer
# meets the validated limits. Give a new/stale selection the recommendation.
if st.session_state.get("optimization_lorry_select") not in lorry_map:
    st.session_state["optimization_lorry_select"] = initial_recommended_label or next(iter(lorry_map))
lorry_label = st.selectbox("Available Lorry", list(lorry_map), key="optimization_lorry_select")
lorry = lorry_map[lorry_label]
a, b, c, d = st.columns(4)
with a: info_card("Plate Number", lorry["plate_number"])
with b: info_card("Internal Size", f"{lorry['internal_length']:g} × {lorry['internal_width']:g} × {lorry['internal_height']:g} cm")
with c: info_card("Maximum Weight", f"{lorry['max_weight']:,.0f} kg")
with d: info_card("Status", lorry["status"])

st.divider()
st.markdown("## Step 3 — Select Eligible Orders")
orders = eligible_orders_for_optimization(point["collection_point_id"])
if not orders:
    if eligible_orders_for_optimization():
        st.info(
            "No eligible orders are assigned to this collection point. "
            "Select the collection point assigned to a Ready for Loading order to create its loading plan."
        )
    else:
        st.info(
            "No orders are ready for a loading plan yet. "
            "First confirm a paid Pending order in Customer Orders, then save its box requirement. "
            "The order will appear here when it is Ready for Loading."
        )
    st.stop()

order_rows = [{
    "Select": True,
    "Order": f"#{o['order_id']}",
    "Customer": o["customer_name"],
    "Status": o["status"],
    "Required Boxes": int(o["required_boxes"]),
    "Estimated Weight": f"{float(o['estimated_weight']):g} kg",
} for o in orders]
selected_rows = render_data_editor(
    pd.DataFrame(order_rows),
    use_container_width=True,
    hide_index=True,
    key="optimization_order_selection",
    column_config={
        "Select": st.column_config.CheckboxColumn("Select", help="Include this order in the loading plan."),
    },
    disabled=["Order", "Customer", "Status", "Required Boxes", "Estimated Weight"],
)
selected_orders = [
    orders[index]["order_id"]
    for index, row in selected_rows.iterrows()
    if bool(row["Select"])
]

# Weight is checked before the optimizer is run. This gives Staff an immediate
# explanation and a practical alternative instead of producing a failed plan.
selected_weight = sum(
    float(order["estimated_weight"] or 0)
    for order in orders
    if order["order_id"] in selected_orders
)
suitable_lorries = sorted(
    (item for item in lorries if float(item["max_weight"]) + 1e-9 >= selected_weight),
    key=lambda item: (float(item["max_weight"]), item["plate_number"]),
)
recommended_lorry = suitable_lorries[0] if suitable_lorries and selected_orders else None
lorry_capacity = float(lorry["max_weight"])
lorry_overloaded = bool(selected_orders and selected_weight > lorry_capacity + 1e-9)

capacity_a, capacity_b, capacity_c, capacity_d = st.columns(4)
capacity_a.metric("Selected Order Weight", f"{selected_weight:,.0f} kg")
capacity_b.metric("Selected Lorry", lorry["plate_number"])
capacity_c.metric("Lorry Maximum", f"{lorry_capacity:,.0f} kg")
capacity_d.metric("Remaining Capacity", f"{max(lorry_capacity - selected_weight, 0):,.0f} kg")

if selected_orders and recommended_lorry:
    st.success(
        f"Recommended lorry: {recommended_lorry['plate_number']} "
        f"({float(recommended_lorry['max_weight']):,.0f} kg capacity). "
        "It is the smallest available lorry that can safely carry the selected orders."
    )
elif selected_orders:
    st.error(
        f"No available lorry can carry the selected {selected_weight:,.0f} kg. "
        "Add a larger lorry profile or reduce the selected orders."
    )

if lorry_overloaded:
    st.error(
        f"{lorry['plate_number']} cannot be used: selected orders weigh "
        f"{selected_weight:,.0f} kg, exceeding its {lorry_capacity:,.0f} kg maximum by "
        f"{selected_weight - lorry_capacity:,.0f} kg. Choose the recommended lorry."
    )

st.divider()
st.markdown("## Step 4 — Review Standardized Box Requirements")
requirements = get_requirements_for_orders(selected_orders)
if requirements:
    totals_by_order = {}
    for r in requirements:
        oid = int(r["order_id"])
        totals_by_order[oid] = totals_by_order.get(oid, 0) + int(r["quantity"])

    order_box_counter = {}
    box_rows = []
    global_box_no = 0
    for r in requirements:
        oid = int(r["order_id"])
        for _ in range(int(r["quantity"])):
            global_box_no += 1
            order_box_counter[oid] = order_box_counter.get(oid, 0) + 1
            per_order_no = order_box_counter[oid]
            box_label = f"O{oid}-B{per_order_no:02d}"
            box_rows.append({
                "Box No.": global_box_no,
                "Box Label": box_label,
                "Order": f"#{oid}",
                "Box Size": f"{int(r['capacity_litre'])}L",
                "Dimensions": f"{r['length']:g} × {r['width']:g} × {r['height']:g} cm",
                "Approx. Load": f"{float(r['loaded_weight_per_box']):.1f} kg",
                "Remark": f"Customer: {r['customer_name']} · Box {per_order_no} of {totals_by_order[oid]}",
            })

    st.info(
        "Each physical box receives a unique AquaLoad Box Label. Mark or print this label on the box during packing. "
        "The same label and customer name are shown again in the 3D Loading Visualization and Loading Sequence."
    )
    req_df = pd.DataFrame(box_rows)
    render_dataframe(req_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download Box Labels CSV",
        req_df.to_csv(index=False).encode("utf-8"),
        file_name=f"aquaload_box_labels_{point['city'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("Select at least one order to review its box requirements.")

st.divider()
st.markdown("## Step 5 — Generate Optimized Loading Plan")

if st.button(
    "Generate Optimized Plan",
    type="primary",
    use_container_width=True,
    disabled=not selected_orders or lorry_overloaded or not recommended_lorry,
):
    with st.spinner("Generating optimized loading plan..."):
        result = preview_optimization(lorry["lorry_id"], selected_orders)
        result["ui_signature"] = [lorry["lorry_id"], sorted(selected_orders)]
    st.session_state.optimization_preview = result

result = st.session_state.get("optimization_preview")
current_signature = [lorry["lorry_id"], sorted(selected_orders)]
if result and result.get("ui_signature") == current_signature:
    st.divider()
    st.markdown("## Optimization Result")
    if not result.get("success"):
        st.error(result.get("message", "No valid arrangement could be generated."))
    else:
        m = result["metrics"]
        st.success("Valid loading arrangement generated.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Boxes", m["total_boxes"])
        c2.metric("Weight Utilization", f"{m['weight_utilization']:.1f}%")
        c3.metric("Loaded Weight", f"{m['total_weight']:,.1f} kg")
        c4.metric("Remaining Weight", f"{m['remaining_weight_capacity']:,.1f} kg")

        space_a, space_b, space_c = st.columns(3)
        space_a.metric("Box Volume Used", f"{m['space_utilization']:.1f}%")
        space_b.metric("Usable Lorry Space", f"{m['lorry_volume'] / 1_000_000:,.2f} m³")
        space_c.metric("Remaining Space", f"{m['remaining_volume'] / 1_000_000:,.2f} m³")

        preview = pd.DataFrame([{
            "Sequence": p["sequence_number"],
            "Box Label": p.get("box_label", f"O{p['order_id']}-B{p['box_instance']:02d}"),
            "Order": f"#{p['order_id']}",
            "Customer": p.get("customer_name", "Customer"),
            "Box": p["box_name"],
            "Placed Size": f"{p['placed_length']:g} × {p['placed_width']:g} × {p['placed_height']:g} cm",
            "Loaded Weight": f"{p['loaded_weight']:.1f} kg",
        } for p in result["placements"]])
        render_dataframe(preview, use_container_width=True, hide_index=True)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Regenerate", use_container_width=True):
                with st.spinner("Regenerating plan..."):
                    regenerated = preview_optimization(lorry["lorry_id"], selected_orders)
                    regenerated["ui_signature"] = [lorry["lorry_id"], sorted(selected_orders)]
                if regenerated.get("success") and _placement_signature(regenerated) == _placement_signature(result):
                    st.session_state.optimization_preview = result
                    flash("info", "This is already the best valid loading plan. No changes were needed.")
                elif regenerated.get("success"):
                    st.session_state.optimization_preview = regenerated
                    flash("success", "A different valid loading plan was generated successfully.")
                else:
                    st.session_state.optimization_preview = regenerated
                    flash("error", regenerated.get("message", "The loading plan could not be regenerated."))
                st.rerun()
        with b2:
            if st.button("Preview 3D Loading Plan", icon=":material/view_in_ar:", type="primary", use_container_width=True):
                # Opening the preview must not reserve inventory or mark orders
                # as loaded. The administrator approves that only after review.
                st.session_state.loading_plan_preview = result
                st.switch_page("pages/loading_visualization.py")
                ok, msg, plan_id = save_optimization(result, st.session_state.user_id, mark_loaded=True)
                if ok:
                    st.session_state.selected_plan_id = plan_id
                    st.session_state.optimization_preview = None
                    flash("success", msg)
                    st.switch_page("pages/loading_visualization.py")
                else:
                    st.error(msg)
