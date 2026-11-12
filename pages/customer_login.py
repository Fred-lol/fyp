import base64
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.auth_session import start_authenticated_session
from components.public_login_layout import render_public_login_header
from constants import ROLES
from services.auth_service import authenticate_user


bootstrap_app()
st.set_page_config(page_title="Customer Login | AquaLoad", page_icon="C", layout="wide", initial_sidebar_state="collapsed")
logo_data = "data:image/png;base64," + base64.b64encode((PROJECT_DIR / "AquaLoad.png").read_bytes()).decode("utf-8")
render_public_login_header(logo_data, "AquaLoad customer access", "Customer Login", "Sign in to browse seafood, place orders and track your order status.")

if reset_message := st.session_state.pop("password_reset_success", None):
    st.success(f"{reset_message} Please sign in with your new password.")

with st.form("customer_login_form", border=True):
    email = st.text_input("Email address", placeholder="Enter your registered email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submitted = st.form_submit_button("Login to Customer Portal", type="primary", use_container_width=True)

if submitted:
    if not email.strip() or not password:
        st.error("Enter both your email address and password.")
    else:
        user, error = authenticate_user(email, password)
        if error:
            st.error(error)
        elif user["role"] != ROLES["CUSTOMER"]:
            st.error("This is a staff account. Please use the Staff Login page.")
        else:
            start_authenticated_session(email, user)

first, second, third = st.columns(3)
with first:
    if st.button("Create customer account", use_container_width=True):
        st.switch_page("pages/register.py")
with second:
    if st.button("Forgot password", use_container_width=True):
        st.switch_page("pages/forgot_password.py")
with third:
    st.link_button("Back to homepage", "/", use_container_width=True)

st.html('<div class="aq-login-help">Are you an AquaLoad staff member? Use <a href="/staff_login">Staff Login</a> to access warehouse and loading operations.</div>')
