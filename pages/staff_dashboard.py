import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import staff_sidebar, require_staff
from components.cards import metric_card
from services.dashboard_service import staff_dashboard_summary

bootstrap_app()
st.set_page_config(page_title="Staff Dashboard | AquaLoad", page_icon="🚚", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
page_header(
    "AquaLoad Operations",
    f"Welcome, {st.session_state.get('user_name','Staff')}. All authorized AquaLoad Staff roles share the same operational functions.",
    "Staff Dashboard",
)

summary = staff_dashboard_summary()

cols = st.columns(6)
with cols[0]: metric_card("Active Orders", summary["active_orders"])
with cols[1]: metric_card("Seafood Products", summary["seafood_products"])
with cols[2]: metric_card("Low / No Stock", summary["low_or_no_stock"])
with cols[3]: metric_card("Available Lorries", summary["available_lorries"])
with cols[4]: metric_card("Available Boxes", summary["available_boxes"])
with cols[5]: metric_card("Saved Plans", summary["saved_plans"])

st.subheader("Quick Actions", anchor=False)
r1 = st.columns(4)
with r1[0]:
    if st.button("Manage Seafood", icon=":material/set_meal:", type="primary", use_container_width=True): st.switch_page("pages/manage_seafood.py")
with r1[1]:
    if st.button("Manage Orders", icon=":material/receipt_long:", type="primary", use_container_width=True): st.switch_page("pages/manage_orders.py")
with r1[2]:
    if st.button("Lorry Tracking", icon=":material/location_on:", type="primary", use_container_width=True): st.switch_page("pages/lorry_tracking.py")
with r1[3]:
    if st.button("Box Inventory", icon=":material/inventory_2:", type="primary", use_container_width=True): st.switch_page("pages/box_profiles.py")
r2 = st.columns(4)
with r2[0]:
    if st.button("Generate Loading Plan", icon=":material/auto_awesome:", type="primary", use_container_width=True): st.switch_page("pages/space_optimization.py")
with r2[1]:
    if st.button("View 3D Loading Plan", icon=":material/view_in_ar:", type="primary", use_container_width=True): st.switch_page("pages/loading_visualization.py")
with r2[2]:
    if st.button("Reports & Analytics", icon=":material/monitoring:", type="primary", use_container_width=True): st.switch_page("pages/reports_analytics.py")
with r2[3]:
    if st.button("User Accounts", icon=":material/group:", type="primary", use_container_width=True): st.switch_page("pages/manage_users.py")
