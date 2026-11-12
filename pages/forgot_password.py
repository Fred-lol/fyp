import re
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.password_feedback import render_password_feedback
from services.auth_service import validate_password_strength
from services.password_reset_service import (
    complete_password_reset,
    request_password_reset_otp,
    verify_password_reset_otp,
)


bootstrap_app()
st.set_page_config(page_title="Reset Password | AquaLoad", page_icon="🔐", layout="wide", initial_sidebar_state="collapsed")

if "recovery_step" not in st.session_state:
    st.session_state.recovery_step = 1
if "recovery_email" not in st.session_state:
    st.session_state.recovery_email = ""
if "recovery_verified" not in st.session_state:
    st.session_state.recovery_verified = False
if "recovery_verification_token" not in st.session_state:
    st.session_state.recovery_verification_token = None

st.html("""
<style>
html,body{margin:0!important;padding:0!important;background:#f6fbfc!important}.stApp{min-height:100vh;background:linear-gradient(135deg,#f4fbfc 0%,#fff 50%,#eef8f7 100%)!important;color:#173b58!important}header[data-testid="stHeader"],[data-testid="stSidebar"]{display:none!important}[data-testid="stMainBlockContainer"],.block-container{max-width:1080px!important;padding:44px 32px 52px!important}
.aq-recovery-logo{display:block;width:145px;height:100px;margin:0 auto 0;object-fit:contain}.aq-recovery-layout{margin-top:0;text-align:center}.aq-eyebrow{color:#008d91;font-size:11px;font-weight:850;letter-spacing:1.9px;text-transform:uppercase}.aq-recovery-title{margin:13px 0 15px;color:#063b63;font-size:46px;font-weight:800;line-height:1.08;letter-spacing:-1.7px}.aq-recovery-description{margin:0 auto;color:#627d8e;font-size:16px;line-height:1.75;max-width:540px}.aq-card-top{padding-bottom:16px;border-bottom:1px solid #e3eeee}.aq-card-top h2{margin:0;color:#073b63;font-size:20px}.aq-card-top p{margin:7px 0 0;color:#708996;font-size:13px;line-height:1.55}.aq-steps{display:flex;gap:0;padding:18px 0 20px}.aq-step{flex:1;display:flex;align-items:center;gap:9px;color:#8197a2;font-size:11px;font-weight:750}.aq-step:not(:last-child):after{content:"";height:1px;flex:1;margin:0 12px;background:#d7e6e6}.aq-step-number{display:grid;place-items:center;width:22px;height:22px;border:1px solid #bfd4d5;border-radius:50%;font-size:10px}.stTextInput label{color:#163d58!important;font-size:13px!important;font-weight:700!important}.stTextInput input{min-height:48px!important;border:1px solid #cfdee3!important;border-radius:8px!important;color:#173b58!important;background:#fff!important;-webkit-text-fill-color:#173b58!important}.stTextInput input:focus{border-color:#0b999c!important;box-shadow:0 0 0 2px rgba(0,156,154,.1)!important}.stTextInput input::placeholder{color:#aebdc5!important;opacity:1!important;-webkit-text-fill-color:#aebdc5!important;font-weight:400!important}.stButton>button[kind="primary"]{min-height:48px!important;border:none!important;border-radius:8px!important;background:#063b63!important;color:#fff!important;font-size:13px!important;font-weight:800!important}.stButton>button[kind="primary"]:hover{background:#087d91!important}[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid #d6e5e5!important;border-radius:14px!important;background:#fff!important;box-shadow:0 18px 42px rgba(8,57,77,.08)!important}.aq-field-help{margin:4px 0 16px;color:#718997;font-size:12px;line-height:1.55}.aq-email-display{padding:12px 14px;border:1px solid #dbe9e8;border-radius:8px;background:#f5fbfa;color:#0d5667;font-size:13px;font-weight:700}.aq-ui-notice{display:none!important}@media(max-width:800px){[data-testid="stMainBlockContainer"],.block-container{padding:28px 20px 40px!important}.aq-recovery-layout{margin-top:0}.aq-recovery-title{font-size:38px}}@media(max-width:480px){.aq-recovery-title{font-size:33px}.aq-step:not(:last-child):after{margin:0 6px}}
</style>
""")

# Match the primary action treatment used by the customer and staff login forms.
st.html("""
<style>
.stButton>button[kind="primary"]{min-height:58px!important;margin-top:12px!important;border:none!important;border-radius:13px!important;color:#fff!important;background:linear-gradient(135deg,#087ead,#0db4b9)!important;font-size:17px!important;font-weight:800!important;box-shadow:0 11px 24px rgba(0,135,155,.18)!important}.stButton>button[kind="primary"] p,.stButton>button[kind="primary"] span{color:#fff!important}
</style>
""")

import base64
logo_data = base64.b64encode((PROJECT_DIR / "AquaLoad.png").read_bytes()).decode("ascii")

RECOVERY_INTRO = f"""
<img src="data:image/png;base64,{logo_data}" class="aq-recovery-logo" alt="AquaLoad logo">
<section class="aq-recovery-layout">
  <div class="aq-recovery-intro">
    <div class="aq-eyebrow">Account recovery</div>
    <h1 class="aq-recovery-title">Reset your password securely.</h1>
    <p class="aq-recovery-description">Enter the email address registered to your AquaLoad account. We will use a one-time passcode to confirm that you own the account before a new password can be set.</p>
  </div>
</section>
"""


def _steps_html(step: int) -> None:
    first = "done" if step == 2 else "active"
    second = "active" if step == 2 else ""
    st.html(f'''<style>.aq-step:nth-child(1){{color:{'#087c83' if step == 2 else '#087c83'}}}.aq-step:nth-child(1) .aq-step-number{{border-color:{'#0c9b94' if step == 2 else '#087c83'};background:{'#e9f8f5' if step == 2 else '#087c83'};color:{'#087c83' if step == 2 else '#fff'}}}.aq-step:nth-child(2){{color:{'#087c83' if step == 2 else '#8197a2'}}}.aq-step:nth-child(2) .aq-step-number{{border-color:{'#087c83' if step == 2 else '#bfd4d5'};background:{'#087c83' if step == 2 else 'transparent'};color:{'#fff' if step == 2 else 'inherit'}}}</style>''')


@st.fragment
def recovery_workspace():
    with st.container(border=True):
        st.html('<div class="aq-card-top"><h2>Password recovery</h2><p>Complete the two short steps to regain access.</p></div>')
        st.html('<div class="aq-steps"><div class="aq-step"><span class="aq-step-number">1</span>Email</div><div class="aq-step"><span class="aq-step-number">2</span>Verify &amp; reset</div></div>')
        _steps_html(st.session_state.recovery_step)
        if st.session_state.recovery_step == 1:
            st.subheader("Confirm your email", anchor=False)
            email = st.text_input("Email address", value=st.session_state.recovery_email, placeholder="name@example.com", autocomplete="email")
            st.html('<div class="aq-field-help">Use the email address registered to your AquaLoad account.</div>')
            if st.button("Request one-time passcode", type="primary", use_container_width=True):
                if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
                    st.error("Enter a valid email address to continue.")
                else:
                    ok, message = request_password_reset_otp(email)
                    if ok:
                        st.session_state.recovery_email = email.strip().lower()
                        st.session_state.recovery_step = 2
                        st.session_state.recovery_verified = False
                        st.session_state.recovery_verification_token = None
                        st.success(message)
                        st.rerun(scope="app")
                    else:
                        st.error(message)
        else:
            st.subheader("Verify your email", anchor=False)
            st.html(f'<div class="aq-email-display">{st.session_state.recovery_email}</div>')
            if not st.session_state.recovery_verified:
                st.caption("Enter the six-digit passcode sent to this email address.")
                otp = st.text_input("One-time passcode", placeholder="Enter the 6-digit code", max_chars=6, autocomplete="one-time-code")
                if st.button("Verify passcode", type="primary", use_container_width=True):
                    ok, message, token = verify_password_reset_otp(st.session_state.recovery_email, otp)
                    if ok:
                        st.session_state.recovery_verified = True
                        st.session_state.recovery_verification_token = token
                        st.success(message)
                        st.rerun(scope="app")
                    else:
                        st.error(message)
            else:
                st.success("Email verified. Create your new password below.")
                new_password = st.text_input("New password", type="password", placeholder="Create a strong password", autocomplete="new-password")
                render_password_feedback(new_password)
                confirm_password = st.text_input("Confirm new password", type="password", placeholder="Enter the password again", autocomplete="new-password")
                if confirm_password:
                    if new_password == confirm_password and validate_password_strength(new_password)[0]:
                        st.success("Passwords match and meet the security requirements.")
                    elif new_password != confirm_password:
                        st.warning("Passwords do not match.")
                if st.button("Reset password", type="primary", use_container_width=True):
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        ok, message = complete_password_reset(
                            st.session_state.recovery_email,
                            st.session_state.recovery_verification_token,
                            new_password,
                        )
                        if ok:
                            st.session_state.recovery_step = 1
                            st.session_state.recovery_email = ""
                            st.session_state.recovery_verified = False
                            st.session_state.recovery_verification_token = None
                            st.session_state.password_reset_success = message
                            st.switch_page("pages/customer_login.py")
                        else:
                            st.error(message)
            if st.button("Use a different email", use_container_width=True):
                st.session_state.recovery_step = 1
                st.session_state.recovery_verified = False
                st.session_state.recovery_verification_token = None
                st.rerun(scope="app")

left, centre, right = st.columns([1, 1.55, 1])
with centre:
    st.html(RECOVERY_INTRO)
    recovery_workspace()
