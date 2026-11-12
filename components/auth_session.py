import streamlit as st

from constants import ROLES


def start_authenticated_session(email: str, user: dict) -> None:
    """Store the authenticated user once, then route to the correct portal."""
    st.session_state.logged_in = True
    st.session_state.user_id = user["user_id"]
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_role = user["role"]
    st.session_state.user_name = user["full_name"]
    st.session_state.theme_preference = user.get("theme_preference") or "System"

    if user["role"] == ROLES["CUSTOMER"]:
        st.switch_page("pages/customer_dashboard.py")
    st.switch_page("pages/staff_dashboard.py")
