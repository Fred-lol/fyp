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
from constants import STAFF_ROLES
from services.auth_service import authenticate_user


bootstrap_app()
st.set_page_config(page_title="Staff Login | AquaLoad", page_icon="S", layout="wide", initial_sidebar_state="collapsed")
logo_data = "data:image/png;base64," + base64.b64encode((PROJECT_DIR / "AquaLoad.png").read_bytes()).decode("utf-8")
render_public_login_header(logo_data, "AquaLoad staff access", "Staff Portal Login", "Authorised AquaLoad staff can sign in to access warehouse, loading and supplier operations.")

with st.form("staff_login_form", border=True):
    email = st.text_input("Staff email address", placeholder="Enter your staff email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submitted = st.form_submit_button("Login to Staff Portal", type="primary", use_container_width=True)

if submitted:
    if not email.strip() or not password:
        st.error("Enter both your email address and password.")
    else:
        user, error = authenticate_user(email, password)
        if error:
            st.error(error)
        elif user["role"] not in STAFF_ROLES:
            st.error("This is a customer account. Please use the Customer Login page.")
        else:
            start_authenticated_session(email, user)

first, second = st.columns(2)
with first:
    if st.button("Forgot password", use_container_width=True):
        st.switch_page("pages/forgot_password.py")
with second:
    st.link_button("Back to homepage", "/", use_container_width=True)

st.info("Staff accounts are issued by authorised AquaLoad administration. Public staff registration is not available.")
