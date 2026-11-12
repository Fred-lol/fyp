"""The exact public header/footer markup shared by homepage and public pages."""

import base64
from pathlib import Path

import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent.parent


def _logo_data() -> str:
    raw = base64.b64encode((PROJECT_DIR / "AquaLoad.png").read_bytes()).decode("ascii")
    return f"data:image/png;base64,{raw}"


def render_homepage_header(*, standalone: bool = True) -> None:
    """Render the literal homepage navigation markup on any public page."""
    css = "<style>.navbar a,.navbar .nav-links a{text-decoration:none!important}</style>" if not standalone else """
    <style>
    [data-testid="stSidebar"]{display:none}
    .navbar{min-height:76px;padding:0 7%;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:9999;width:100vw;box-sizing:border-box;margin:0 0 42px calc(50% - 50vw);background:rgba(255,255,255,.96);border-bottom:1px solid #dce9e5;backdrop-filter:blur(14px);box-shadow:none}.logo{display:flex;align-items:center}.logo img{width:172px;height:78px;max-height:54px;object-fit:contain}.nav-links{display:flex;align-items:center;gap:27px}.navbar a,.navbar .nav-links a{position:relative;color:#3b5965;text-decoration:none!important;font-size:12px!important;font-weight:700!important;line-height:1.2!important;letter-spacing:.01em;transition:.2s ease}.nav-links a:not(.staff-nav)::after{content:"";position:absolute;left:0;bottom:-8px;width:0;height:2px;background:#00aeb7;transition:.2s ease}.nav-links a:hover{color:#087ab0}.nav-links a:hover::after{width:100%}.staff-nav{padding:11px 18px!important;border:1px solid #062e55!important;border-radius:5px;color:#fff!important;background:#062e55!important;box-shadow:0 2px 0 rgba(0,0,0,.08)}.staff-nav:hover{color:#fff!important;border-color:#087ab0!important;background:#087ab0!important}@media(max-width:700px){.navbar{padding:0 1rem;margin-bottom:28px}.logo img{width:128px;max-height:46px}.nav-links{gap:12px}.nav-links a:not(.staff-nav){display:none}.staff-nav{padding:9px 12px!important}}
    </style>
    """
    st.html(css + f'''<nav class="navbar"><a class="logo" href="/" style="text-decoration:none!important"><img src="{_logo_data()}" alt="AquaLoad Logo"></a><div class="nav-links"><a href="/" style="text-decoration:none!important">Home</a><a href="/about_aquaload" style="text-decoration:none!important">About AquaLoad</a><a href="/who_we_serve" style="text-decoration:none!important">Who We Serve</a><a href="/staff_login" target="_self" class="staff-nav" style="text-decoration:none!important">Staff Entry</a></div></nav>''')


def render_homepage_footer(*, standalone: bool = True) -> None:
    """Render the literal homepage footer markup on any public page."""
    css = "" if not standalone else """
    <style>
    .aquaload-footer{min-height:104px;box-sizing:border-box;width:100vw;margin:64px 0 0 calc(50% - 50vw);padding:20px 7%;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:28px;background:#041e2a;color:#8197a7}.footer-logo img{width:132px;height:58px;object-fit:contain}.footer-center{text-align:center}.footer-center strong{display:block;margin-bottom:5px;color:#fff;font-size:13px}.footer-center span{color:#9bb3bc;font-size:10px}.footer-right{text-align:right}.footer-right strong{display:block;color:#b9f0e8;font-size:11px}.footer-right span{display:block;margin-top:4px;color:#9bb3bc;font-size:10px}.footer-bottom{box-sizing:border-box;width:100vw;margin:0 0 -3rem calc(50% - 50vw);padding:11px 7%;border-top:1px solid rgba(255,255,255,.05);text-align:center;color:#8fa9b2;background:#031b26;font-size:10px}@media(max-width:700px){.aquaload-footer{grid-template-columns:1fr;gap:12px;padding:20px 1rem}.footer-center,.footer-right{text-align:left}.footer-bottom{padding-left:1rem;padding-right:1rem}}
    </style>
    """
    st.html(css + f'''<div class="aquaload-footer"><div class="footer-logo"><img src="{_logo_data()}" alt="AquaLoad Logo"></div><div class="footer-center"><strong>AquaLoad</strong><span>Malaysian Seafood Ordering &amp; Smart Loading Platform</span></div><div class="footer-right"><strong>Smarter Loads · Fresher Seafood</strong><span>Space Optimization System</span></div></div><div class="footer-bottom">© 2026 AquaLoad · Final Year Project</div>''')
