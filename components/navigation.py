from base64 import b64encode
from functools import lru_cache
from pathlib import Path

import streamlit as st
from constants import ROLES, STAFF_ROLES


PROJECT_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = PROJECT_DIR / "AquaLoad.png"


@lru_cache(maxsize=1)
def _sidebar_logo_data_url():
    encoded = b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _clear_session():
    for key in [
        "logged_in", "user_id", "user_email", "user_role", "user_name",
        "selected_order_id", "selected_plan_id", "optimization_preview", "loading_plan_preview",
        "portal_mode", "theme_preference", "cart", "checkout_cart", "last_paid_order_id"
    ]:
        st.session_state.pop(key, None)


def require_login():
    if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
        # Keep an expired session clear and contained instead of showing a
        # page-wide alert banner. This is rendered before any portal content.
        st.html("""
        <section class="aq-session-card" role="status" aria-label="Session expired">
          <div class="aq-session-icon" aria-hidden="true">&#128274;</div>
          <div>
            <div class="aq-session-title">Session Expired</div>
            <p>Your session has ended. Please sign in again to continue.</p>
          </div>
        </section>
        """)
        if st.button("Back to Login", type="primary", key="session_expired_login"):
            st.switch_page("homepage.py")
        st.stop()


def require_role(*allowed_roles):
    require_login()
    if st.session_state.get("user_role") not in allowed_roles:
        st.error("You are not authorized to access this page.")
        st.stop()


def require_staff():
    require_role(*STAFF_ROLES)


def customer_sidebar():
    require_role(ROLES["CUSTOMER"])
    with st.sidebar:
        st.html(
            f'<div class="aq-sidebar-logo">'
            f'<img src="{_sidebar_logo_data_url()}" alt="AquaLoad" draggable="false" '
            'style="display:block;width:76px;height:auto;" /></div>'
        )
        st.markdown("## AquaLoad")
        st.caption(st.session_state.get("user_name", "Customer"))
        st.divider()
        st.page_link("pages/customer_dashboard.py", label="Dashboard", icon=":material/dashboard:")
        st.page_link("pages/order_seafood.py", label="Order Seafood", icon=":material/set_meal:")
        st.page_link("pages/my_orders.py", label="My Orders", icon=":material/receipt_long:")
        st.page_link("pages/track_order.py", label="Track Order", icon=":material/location_on:")
        st.page_link("pages/profile.py", label="My Profile", icon=":material/person:")
        st.divider()
        if st.button("Logout", use_container_width=True, key="customer_logout"):
            _clear_session()
            st.switch_page("homepage.py")


def staff_sidebar(keep_loading_preview=False):
    require_staff()
    # A generated plan is only a review draft. It must never remain available
    # after staff leave the 3D review page without approving it.
    if not keep_loading_preview:
        st.session_state.pop("loading_plan_preview", None)
    role = st.session_state.get("user_role")
    with st.sidebar:
        st.html(
            f'<div class="aq-sidebar-logo">'
            f'<img src="{_sidebar_logo_data_url()}" alt="AquaLoad" draggable="false" '
            'style="display:block;width:76px;height:auto;" /></div>'
        )
        st.markdown("## AquaLoad Operations")
        st.caption(st.session_state.get("user_name", "Staff"))
        st.caption(role)
        st.divider()
        st.page_link("pages/staff_dashboard.py", label="Dashboard", icon=":material/dashboard:")
        st.markdown("##### SEAFOOD & ORDERS")
        st.page_link("pages/manage_seafood.py", label="Seafood Management", icon=":material/set_meal:")
        st.page_link("pages/manage_orders.py", label="Customer Orders", icon=":material/receipt_long:")
        st.page_link("pages/order_status_management.py", label="Order Status", icon=":material/published_with_changes:")
        st.page_link("pages/lorry_tracking.py", label="Lorry Tracking", icon=":material/location_on:")
        st.markdown("##### LOADING RESOURCES")
        st.page_link("pages/lorry_profiles.py", label="Lorry Profiles", icon=":material/local_shipping:")
        st.page_link("pages/box_profiles.py", label="Box Profiles", icon=":material/inventory_2:")
        st.markdown("##### LOADING PLANNING")
        st.page_link("pages/space_optimization.py", label="Space Optimization", icon=":material/grid_view:")
        st.page_link("pages/loading_visualization.py", label="3D Loading Plan", icon=":material/view_in_ar:")
        st.markdown("##### REPORTING")
        st.page_link("pages/reports_analytics.py", label="Reports & Analytics", icon=":material/bar_chart:")
        st.markdown("##### SYSTEM")
        st.page_link("pages/manage_users.py", label="User Accounts", icon=":material/group:")
        st.page_link("pages/profile.py", label="My Profile", icon=":material/person:")
        st.divider()
        if st.button("Logout", use_container_width=True, key="staff_logout"):
            _clear_session()
            st.switch_page("homepage.py")
