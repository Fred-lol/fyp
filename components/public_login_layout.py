import streamlit as st
from components.alert_theme import apply_alert_theme


LOGIN_CSS = """
<style>
html, body { margin:0!important; padding:0!important; overflow-x:hidden!important; }
.stApp { min-height:100vh; background:radial-gradient(circle at 8% 10%,rgba(0,174,183,.07),transparent 25%),radial-gradient(circle at 92% 90%,rgba(0,63,114,.06),transparent 25%),linear-gradient(180deg,#edf6f8 0%,#f8fbfc 100%)!important; }
header[data-testid="stHeader"], [data-testid="stSidebar"] { display:none!important; }
[data-testid="stMain"] { padding:0!important; }
[data-testid="stMainBlockContainer"], .block-container { width:100%!important; max-width:900px!important; margin:0 auto!important; padding:32px 28px 25px!important; }
.aq-login-header { max-width:760px; margin:0 auto; text-align:center; }
.aq-login-logo { display:block; width:145px; height:100px; margin:0 auto 6px; object-fit:contain; }
.aq-eyebrow { margin-bottom:8px; color:#009ba4; font-size:11px; font-weight:800; letter-spacing:2px; text-transform:uppercase; }
.aq-title { margin:0; color:#0b3958; font-size:44px; font-weight:800; line-height:1.15; letter-spacing:-1.2px; }
.aq-description { max-width:650px; margin:13px auto 25px; color:#6e8491; font-size:14px; line-height:1.7; }
.stButton { width:100%; }
.stButton button, .stLinkButton a { width:100%; min-height:46px; padding:7px 14px; border:1px solid #cadce4!important; border-radius:11px!important; color:#28516a!important; background:#ffffff!important; font-size:13px!important; font-weight:700!important; box-shadow:0 3px 8px rgba(20,70,90,.025); transition:all .2s ease; }
.stButton button:hover, .stLinkButton a:hover { border-color:#83cbd0!important; color:#008f97!important; background:#f4fbfb!important; transform:translateY(-1px); }
[data-testid="stForm"] { max-width:720px; margin:25px auto 0; padding:30px 34px 33px; border:1px solid #d6e4e9!important; border-radius:23px!important; background:rgba(255,255,255,.98)!important; box-shadow:0 16px 42px rgba(9,54,75,.075); }
.stTextInput label { color:#284c63!important; font-size:13px!important; font-weight:700!important; }
.stTextInput input { min-height:51px!important; padding:0 15px!important; border:1px solid #d3e1e7!important; border-radius:11px!important; color:#173a50!important; background:#fbfdfe!important; font-size:14px!important; }
.stTextInput input:focus { border-color:#00a8af!important; box-shadow:0 0 0 3px rgba(0,168,175,.08)!important; }
[data-testid="stFormSubmitButton"] { width:100%!important; }
[data-testid="stFormSubmitButton"] button { width:100%!important; min-height:58px!important; margin-top:12px; border:none!important; border-radius:13px!important; color:#ffffff!important; background:linear-gradient(135deg,#087ead,#0db4b9)!important; font-size:17px!important; font-weight:800!important; box-shadow:0 11px 24px rgba(0,135,155,.18); }
[data-testid="stFormSubmitButton"] button p, [data-testid="stFormSubmitButton"] button span { color:#ffffff!important; }
@media(max-width:700px) { [data-testid="stMainBlockContainer"], .block-container { padding:22px 17px 20px!important; } .aq-title { font-size:35px; } .aq-description { font-size:13px; } [data-testid="stForm"] { padding:23px 19px 25px; border-radius:17px!important; } }
</style>
"""


def render_public_login_header(logo_data: str, eyebrow: str, title: str, description: str) -> None:
    apply_alert_theme()
    st.html(
        f"""{LOGIN_CSS}
        <div class="aq-login-header">
          <img src="{logo_data}" class="aq-login-logo" alt="AquaLoad Logo">
          <div class="aq-eyebrow">{eyebrow}</div>
          <div class="aq-title">{title}</div>
          <div class="aq-description">{description}</div>
        </div>
        """
    )
