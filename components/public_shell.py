"""Shared, theme-isolated public website shell and landing-page visuals."""
import base64
from html import escape
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent

PUBLIC_CSS = """
<style>
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#fff!important;color:#173b58!important;overflow-x:clip!important}
[data-testid="stMainBlockContainer"],.block-container{max-width:none!important;padding:0!important}
[data-testid="stSidebar"]{display:none!important}
[data-testid="stHeader"]{background:transparent!important}
.navbar{width:100%;min-height:78px;padding:0 max(24px,calc((100vw - 1280px)/2));display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:9999;box-sizing:border-box;background:rgba(255,255,255,.97);border-bottom:1px solid #e3edf0;backdrop-filter:blur(14px)}
.logo{display:flex;align-items:center;flex:none}.logo img{display:block;width:174px;height:58px;object-fit:contain}
.nav-links{display:flex;align-items:center;gap:30px}.navbar .nav-links a{color:#082e4b!important;text-decoration:none!important;font-size:14px!important;font-weight:650!important;line-height:1.2!important;white-space:nowrap;transition:color .18s ease}
.nav-links a:not(.staff-nav):hover,.nav-links a[aria-current="page"]{color:#008c95!important}.nav-links a[aria-current="page"]:after{content:"";display:block;height:2px;background:#008c95;margin-top:7px}
.navbar .nav-links .staff-nav{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 18px!important;border:1px solid #082e4b!important;border-radius:8px;color:#fff!important;background:#082e4b!important}.navbar .nav-links .staff-nav:hover{color:#fff!important;background:#0b746f!important;border-color:#0b746f!important}
.aq-public-main{width:min(1280px,calc(100% - 64px));margin:0 auto;color:#173b58}
.aq-home-hero{min-height:min(680px,calc(100svh - 238px));padding:clamp(44px,6vw,82px) 0;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(350px,.9fr);gap:clamp(32px,5vw,70px);align-items:center}
.aq-home-copy h1{max-width:760px;margin:18px 0;color:#082e4b;font-size:clamp(44px,5.5vw,76px);font-weight:800;line-height:1.02;letter-spacing:-.045em}.aq-home-copy h1 span{color:#087f7b}.aq-home-copy p{max-width:680px;color:#526e7e;font-size:17px;line-height:1.75;margin:0 0 26px}
.aq-public-kicker{color:#008c95;font-size:12px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
.aq-public-cta{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 20px;border-radius:8px;background:#087eab;color:#fff!important;text-decoration:none!important;font-weight:700;box-shadow:0 8px 18px rgba(8,126,171,.16);transition:background .18s,transform .18s}.aq-public-cta:hover{background:#008c95;transform:translateY(-1px)}
.aq-sample-plan{padding:26px;border:1px solid #0d7a91;border-radius:14px;background:#0a3e60;color:#fff;box-shadow:0 18px 44px rgba(8,46,75,.17)}.aq-sample-plan-head{display:flex;justify-content:space-between;align-items:center;gap:14px;padding-bottom:18px;border-bottom:1px solid rgba(255,255,255,.18);font-weight:750}.aq-sample-tag{padding:8px 11px;border:1px solid #2797aa;border-radius:6px;color:#a8f2ee;font-size:10px;letter-spacing:.09em}.aq-sample-grid{margin-top:18px;padding:22px 18px 14px;border:1px solid #24738d;border-radius:8px;background-color:#082f49;background-image:linear-gradient(rgba(255,255,255,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.055) 1px,transparent 1px);background-size:24px 24px}.aq-sample-label{font-size:11px;color:#a8e3e8;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.aq-sample-boxes{height:220px;box-sizing:border-box;display:grid;grid-template-columns:23fr 33fr 44fr;grid-template-rows:repeat(2,minmax(0,1fr));align-items:stretch;gap:2px;padding:24px 8px 0}.aq-sample-box{height:auto;min-height:0;min-width:0;display:grid;place-items:center;border:1px solid rgba(255,255,255,.28);border-radius:6px;color:#fff;font-weight:800;font-size:14px}.aq-sample-box:nth-child(3n+1){background:#109894}.aq-sample-box:nth-child(3n+2){background:#247eb7}.aq-sample-box:nth-child(3n){background:#c9783b}.aq-sample-ends{display:flex;justify-content:space-between;margin:12px 4px 0;font-size:10px;font-weight:800;letter-spacing:.04em}.aq-sample-ends span:first-child{color:#ffad59}.aq-sample-ends span:last-child{color:#69e1dc}
.aq-sample-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}.aq-sample-metrics div{padding:13px;border:1px solid rgba(255,255,255,.16);border-radius:7px;background:rgba(255,255,255,.07)}.aq-sample-metrics small{display:block;color:#c2dce5;font-size:11px}.aq-sample-metrics strong{display:block;margin-top:7px;color:#9ceee6;font-size:14px}
.aq-capabilities{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;padding:8px 0 64px}.aq-capabilities article,.aq-audience-card{padding:24px;border:1px solid #d8e6eb;border-radius:12px;background:#fff;box-shadow:0 8px 24px rgba(8,46,75,.045)}.aq-capabilities h2,.aq-audience-card h2,.aq-public-section h2{margin:11px 0;color:#082e4b;font-size:23px;line-height:1.2}.aq-capabilities p,.aq-audience-card p,.aq-public-section p{margin:0;color:#536f7d;font-size:15px;line-height:1.7}
.aq-public-intro{padding:clamp(42px,6vw,70px) 0 24px}.aq-public-intro h1{max-width:900px;margin:12px 0;color:#082e4b;font-size:clamp(36px,4.4vw,58px);line-height:1.07;letter-spacing:-.035em}.aq-public-intro p{max-width:820px;color:#536f7d;font-size:17px;line-height:1.7}
.aq-public-section{padding:28px 0 38px}.aq-about-business{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(24px,4vw,54px);align-items:center}.aq-harbour-frame{height:340px;overflow:hidden;border-radius:12px;background:#e8f1f3}.aq-harbour-frame img{width:100%;height:100%;display:block;object-fit:cover}.aq-harbour-unavailable{width:100%;height:100%;display:grid;place-items:center;color:#082e4b;font-size:20px;font-weight:750}.aq-audience-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;padding:22px 0 30px}.aq-audience-card{display:flex;flex-direction:column;align-items:flex-start;min-height:230px}.aq-audience-card .aq-public-cta{margin-top:auto}.aq-workflow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:18px}.aq-workflow span{display:flex;gap:12px;align-items:center;padding:17px;border:1px solid #d8e6eb;border-radius:9px;color:#082e4b;font-weight:700}.aq-workflow small{color:#008c95;font-size:11px;font-weight:800;letter-spacing:.1em}
.aquaload-footer{width:100%;min-height:122px;box-sizing:border-box;padding:22px max(24px,calc((100vw - 1280px)/2));display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:28px;background:#041e2a;color:#8197a7}.footer-logo img{display:block;width:132px;height:58px;object-fit:contain}.footer-center{text-align:center}.footer-center strong{display:block;margin-bottom:5px;color:#fff;font-size:14px}.footer-center span{color:#b0c5ce;font-size:12px}.footer-right{text-align:right}.footer-right strong{display:block;color:#b9f0e8;font-size:12px}.footer-right span{display:block;margin-top:4px;color:#b0c5ce;font-size:11px}.footer-bottom{width:100%;box-sizing:border-box;padding:12px 24px;border-top:1px solid rgba(255,255,255,.07);text-align:center;color:#a8bac3;background:#031b26;font-size:11px}
@media(max-width:900px){.navbar{padding:0 24px}.nav-links{gap:18px}.aq-public-main{width:calc(100% - 48px)}.aq-home-hero{grid-template-columns:1fr;min-height:unset;padding:50px 0;gap:34px}.aq-home-copy h1{max-width:740px}.aq-sample-plan{max-width:700px}.aq-capabilities{padding-bottom:44px}}
@media(max-width:640px){.navbar{min-height:0;padding:11px 16px;flex-wrap:wrap;gap:8px}.logo img{width:136px;height:46px}.nav-links{width:100%;justify-content:space-between;gap:6px}.navbar .nav-links a{font-size:10px!important}.navbar .nav-links .staff-nav{min-height:34px;padding:0 10px!important;font-size:10px!important}.nav-links a[aria-current="page"]:after{margin-top:4px}.aq-public-main{width:calc(100% - 32px)}.aq-home-hero{padding:38px 0}.aq-home-copy h1{font-size:clamp(40px,12vw,58px)}.aq-home-copy p{font-size:15px}.aq-sample-plan{padding:16px}.aq-sample-grid{padding:15px 10px 12px}.aq-sample-boxes{height:176px;padding:20px 2px 0}.aq-sample-box{font-size:12px}.aq-sample-metrics{gap:7px}.aq-sample-metrics div{padding:9px}.aq-sample-metrics small{font-size:10px}.aq-sample-metrics strong{font-size:12px}.aq-capabilities,.aq-audience-grid,.aq-about-business,.aq-workflow{grid-template-columns:1fr}.aq-capabilities{padding-bottom:34px}.aq-public-intro{padding-top:36px}.aq-harbour-frame{height:230px}.aq-audience-card{min-height:200px}.aquaload-footer{grid-template-columns:1fr;gap:12px;padding:20px 16px}.footer-center,.footer-right{text-align:left}.footer-logo img{width:118px;height:48px}.footer-bottom{padding:12px 16px}}
</style>
"""


def _logo_data() -> str:
    raw = base64.b64encode((PROJECT_DIR / "AquaLoad.png").read_bytes()).decode("ascii")
    return f"data:image/png;base64,{raw}"


def render_homepage_header(*, active: str = "Home", standalone: bool = True) -> None:
    """Render the same permanently light public header on every public page."""
    st.html(PUBLIC_CSS)
    links = (("Home", "/"), ("About AquaLoad", "/about_aquaload"), ("Who We Serve", "/who_we_serve"))
    nav = "".join(
        f'<a href="{href}" target="_self" aria-current="{"page" if active == label else "false"}">{escape(label)}</a>'
        for label, href in links
    )
    st.html(
        f'<nav class="navbar"><a class="logo" href="/" target="_self" aria-label="AquaLoad home">'
        f'<img src="{_logo_data()}" alt="AquaLoad Logo"></a><div class="nav-links">{nav}'
        '<a href="/staff_login" target="_self" class="staff-nav">Staff Entry</a></div></nav>'
    )


def render_homepage_footer(*, standalone: bool = True) -> None:
    st.html(
        '<footer class="aquaload-footer"><div class="footer-logo"><img src="'
        f'{_logo_data()}" alt="AquaLoad Logo"></div><div class="footer-center"><strong>AquaLoad</strong>'
        '<span>Malaysian Seafood Ordering &amp; Smart Loading Platform</span></div>'
        '<div class="footer-right"><strong>Smarter Loads &middot; Fresher Seafood</strong>'
        '<span>Space Optimization System</span></div></footer>'
        '<div class="footer-bottom">&copy; 2026 AquaLoad &middot; Final Year Project</div>'
    )


def render_sample_plan() -> str:
    """Return the static homepage illustration; it is explicitly sample-only."""
    labels = "".join(f'<div class="aq-sample-box">{size}</div>' for size in ("20L", "50L", "75L", "20L", "50L", "75L"))
    return (
        '<aside class="aq-sample-plan" aria-label="Sample loading plan illustration">'
        '<div class="aq-sample-plan-head"><span>Sample loading plan</span><span class="aq-sample-tag">SAMPLE ONLY</span></div>'
        '<div class="aq-sample-grid"><div class="aq-sample-label">Insulated box arrangement &middot; 6 positions</div>'
        f'<div class="aq-sample-boxes">{labels}</div>'
        '<div class="aq-sample-ends"><span>REAR LOADING GATE</span><span>DEEPEST END</span></div></div>'
        '<div class="aq-sample-metrics"><div><small>Box positions</small><strong>6 ready</strong></div>'
        '<div><small>Volume used</small><strong>68%</strong></div><div><small>Plan check</small><strong>Clear</strong></div></div>'
        '</aside>'
    )
