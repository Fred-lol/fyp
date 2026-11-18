"""One responsive public shell shared by all public pages."""
from base64 import b64encode
from datetime import date
from pathlib import Path
import streamlit as st
from components.theme import apply_theme

PUBLIC_CSS = """
<style>
[data-testid="stSidebar"],header[data-testid="stHeader"]{display:none!important}
[data-testid="stAppViewContainer"]:has(.aq-public-header),.stApp:has(.aq-public-header){background:var(--aq-bg)!important}
[data-testid="stMainBlockContainer"]{max-width:1280px!important;padding:0 28px 28px!important}
.aq-public-header{height:76px;display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:1px solid var(--aq-border);margin-bottom:40px;background:var(--aq-bg)}
.aq-public-header img{width:172px;height:54px;object-fit:contain}.aq-public-links{display:flex;gap:27px;align-items:center}
.aq-public-header a{color:var(--aq-text)!important;text-decoration:none!important;font-size:15px;font-weight:600}
.aq-public-header a[aria-current="page"],.aq-public-header a:hover{color:var(--aq-teal)!important}
.aq-public-header details{display:none}.aq-public-header summary{cursor:pointer;color:var(--aq-text);font-size:15px}
.aq-public-footer{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:28px;padding:24px 28px;border:1px solid #173d53;border-radius:12px;margin-top:56px;background:#062838;color:#c4dce5;font-size:13px}
.aq-public-footer img{width:132px;height:58px;object-fit:contain}.aq-public-footer-center{text-align:center}.aq-public-footer-right{text-align:right}
.aq-public-footer strong{display:block;font-size:15px;color:#fff;margin-bottom:6px}
.aq-home-hero{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center;padding:16px 0 48px}
.aq-home-hero h1{font-size:clamp(34px,4vw,54px)!important;line-height:1.1!important;letter-spacing:-1.5px;margin:12px 0 22px!important;padding:0!important;color:var(--aq-text)!important}
.aq-home-hero p,.aq-public-intro p{font-size:17px;line-height:1.7;color:var(--aq-muted);max-width:580px}
.aq-public-kicker{font-size:12px;color:var(--aq-teal);font-weight:700;letter-spacing:1.5px;text-transform:uppercase}
.aq-public-cta{display:inline-block;margin-top:20px;background:var(--aq-teal);color:var(--aq-on-primary)!important;text-decoration:none!important;padding:13px 24px;border-radius:8px;font-weight:600}
.aq-sample{padding:24px;border:1px solid var(--aq-border);border-radius:12px;background:var(--aq-card);color:var(--aq-text)}
.aq-sample-top{display:flex;justify-content:space-between;gap:12px;margin-bottom:20px}.aq-sample-top span{font-size:11px;color:var(--aq-muted);letter-spacing:1px}
.aq-sample-bay{display:grid;grid-template-columns:1fr 1.3fr 1.5fr;gap:7px;padding:14px;border:1px solid var(--aq-border);border-radius:6px;background:var(--aq-card2)}
.aq-sample-bay span{display:grid;place-items:center;min-height:78px;border-radius:4px;background:#087d88;color:#fff;font-size:14px;font-weight:600}.aq-sample-bay span:nth-child(3n+2){background:#226c9b}.aq-sample-bay span:nth-child(3n){background:#a35825}
.aq-sample-direction{display:flex;justify-content:space-between;margin-top:12px;font-size:12px;color:var(--aq-muted)}
.aq-capabilities{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;padding:32px 0;border-top:1px solid var(--aq-border)}
.aq-capabilities h2{font-size:21px!important;color:var(--aq-text)!important}.aq-capabilities p{font-size:15px;line-height:1.7;color:var(--aq-muted)}
.aq-public-intro{max-width:900px;margin:12px 0 40px}.aq-public-intro h1{font-size:clamp(32px,4vw,48px)!important;color:var(--aq-text)!important;line-height:1.2!important}
.aq-public-row{display:grid;grid-template-columns:60px 240px 1fr;gap:24px;padding:24px 0;border-top:1px solid var(--aq-border);color:var(--aq-text)}.aq-public-row p{margin:0;color:var(--aq-muted);line-height:1.7}.aq-public-row span{color:var(--aq-teal);font-size:13px}
.aq-public-section{padding:28px 0;border-top:1px solid var(--aq-border)}.aq-public-section h2{font-size:clamp(23px,2.7vw,32px)!important;color:var(--aq-text)!important;margin:0 0 12px!important}.aq-public-section p{color:var(--aq-muted);font-size:16px;line-height:1.7;max-width:700px;margin:0}
.aq-about-business{display:grid;grid-template-columns:1fr 1fr;gap:42px;align-items:center}.aq-harbour-frame{min-height:255px;border-radius:10px;overflow:hidden;background:var(--aq-card2);border:1px solid var(--aq-border)}.aq-harbour-frame img{width:100%;height:100%;min-height:255px;object-fit:cover}.aq-harbour-unavailable{height:255px;display:flex;align-items:center;justify-content:center;text-align:center;padding:20px;color:var(--aq-muted);font-size:14px}
.aq-audience-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:24px 0 34px}.aq-audience-card{padding:28px;border-radius:12px;border:1px solid var(--aq-border);background:var(--aq-card)}.aq-audience-card h2{font-size:25px!important;color:var(--aq-text)!important;margin:0 0 12px!important}.aq-audience-card p{color:var(--aq-muted);line-height:1.65;min-height:78px}.aq-audience-card .aq-public-cta{margin-top:8px}.aq-workflow{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.aq-workflow span{padding:18px;border:1px solid var(--aq-border);background:var(--aq-card2);border-radius:9px;color:var(--aq-text);font-weight:650}.aq-workflow small{display:block;color:var(--aq-teal);margin-bottom:7px}
@media(max-width:800px){.aq-home-hero{grid-template-columns:1fr;gap:28px}.aq-capabilities{grid-template-columns:1fr;gap:16px}.aq-public-row{grid-template-columns:36px 1fr}.aq-public-row p{grid-column:2}.aq-public-footer{grid-template-columns:1fr;gap:12px}.aq-public-footer-center,.aq-public-footer-right{text-align:left}.aq-public-links{display:none}.aq-public-header details{display:block;position:relative}.aq-public-header details[open] .aq-mobile-nav{position:absolute;right:0;top:32px;width:220px;display:grid;gap:20px;padding:24px;background:var(--aq-card);border:1px solid var(--aq-border);border-radius:8px;z-index:10}}
@media(max-width:800px){.aq-about-business,.aq-audience-grid{grid-template-columns:1fr}.aq-audience-card p{min-height:0}.aq-workflow{grid-template-columns:1fr}}
@media(max-width:500px){[data-testid="stMainBlockContainer"]{padding:0 18px 24px!important}.aq-sample{padding:16px}.aq-sample-bay span{min-height:62px}.aq-public-header{margin-bottom:28px}}
</style>
"""


def render_homepage_header(*, active="Home", standalone=True):
    apply_theme()
    st.html(PUBLIC_CSS)
    logo = b64encode((Path(__file__).resolve().parents[1] / "AquaLoad.png").read_bytes()).decode()
    links = [("Home","/"),("About AquaLoad","/about_aquaload"),("Who We Serve","/who_we_serve"),("Staff Entry","/staff_login")]
    nav = ''.join(f'<a href="{href}" target="_self" aria-current="{ "page" if label == active else "false" }">{label}</a>' for label,href in links)
    st.html(f'<header class="aq-public-header"><a href="/" target="_self"><img src="data:image/png;base64,{logo}" alt="AquaLoad"></a><nav class="aq-public-links" aria-label="Public navigation">{nav}</nav><details><summary>Menu</summary><nav class="aq-mobile-nav" aria-label="Mobile navigation">{nav}</nav></details></header>')


def render_homepage_footer(*, standalone=True):
    logo = b64encode((Path(__file__).resolve().parents[1] / "AquaLoad.png").read_bytes()).decode()
    st.html(f'<footer class="aq-public-footer"><div><img src="data:image/png;base64,{logo}" alt="AquaLoad"></div><div class="aq-public-footer-center"><strong>AquaLoad</strong>Malaysian Seafood Ordering &amp; Smart Loading Platform</div><div class="aq-public-footer-right"><strong>Smarter Loads · Fresher Seafood</strong>© {date.today().year} AquaLoad</div></footer>')


def render_sample_plan():
    return '<div class="aq-sample"><div class="aq-sample-top"><strong>Loading arrangement</strong><span>SAMPLE ONLY</span></div><div class="aq-sample-bay"><span>20L</span><span>50L</span><span>75L</span><span>20L</span><span>50L</span><span>75L</span></div><div class="aq-sample-direction"><span>Rear loading gate</span><span>Deepest end &rarr;</span></div></div>'
