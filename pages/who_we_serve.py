import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from components.theme import apply_theme
from components.public_shell import render_homepage_footer, render_homepage_header


st.set_page_config(page_title="Who We Serve | AquaLoad", page_icon="U", layout="wide", initial_sidebar_state="collapsed")
apply_theme("Light")
st.html("""
<style>
[data-testid="stSidebar"]{display:none}.aq-public-nav{display:flex;align-items:center;min-height:76px;margin:0 0 34px;padding:0;border-bottom:1px solid #dce9e5;background:rgba(255,255,255,.96)}.aq-logo-link{display:block;width:172px;height:54px}.aq-logo-link img{display:block;width:172px;height:54px;object-fit:contain;image-rendering:auto}
.aq-kicker,.aq-role-number{color:#008b91;font-size:11px;font-weight:850;letter-spacing:1.75px;text-transform:uppercase}.aq-serve-hero{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(250px,.85fr);gap:58px;padding:0 0 43px;border-bottom:1px solid #d7e7e5}.aq-serve-hero h1{margin:12px 0 16px;color:#073b63;font-size:52px;line-height:1.04;letter-spacing:-2.2px}.aq-serve-hero p{margin:0;color:#587586;font-size:16px;line-height:1.75;max-width:700px}.aq-access-note{align-self:end;border-left:3px solid #0a9a9a;padding:4px 0 4px 20px}.aq-access-note strong{display:block;margin:8px 0;color:#073b63;font-size:18px}.aq-access-note p{font-size:14px;line-height:1.7}
.aq-section-title{margin:46px 0 8px;color:#073b63;font-size:27px;font-weight:800;letter-spacing:-.8px}.aq-section-intro{margin:0 0 26px;color:#607c8a;font-size:14px;line-height:1.7;max-width:720px}.aq-roles{border-top:1px solid #dbe8e6}.aq-role{display:grid;grid-template-columns:72px 250px minmax(0,1fr);gap:20px;align-items:start;padding:25px 0;border-bottom:1px solid #dbe8e6}.aq-role h3{margin:0;color:#073b63;font-size:17px}.aq-role p{margin:0;color:#66808c;font-size:14px;line-height:1.65}.aq-role-number{padding-top:3px}@media(max-width:800px){.aq-serve-hero{grid-template-columns:1fr;gap:26px}.aq-serve-hero h1{font-size:39px}.aq-role{grid-template-columns:54px 1fr}.aq-role p{grid-column:2}}@media(max-width:500px){.aq-serve-hero h1{font-size:34px}}
.aq-public-footer{box-sizing:border-box;width:100vw;margin:64px 0 -3rem calc(50% - 50vw);padding:24px 7% 0;background:#041e2a}.aq-footer-main{display:grid;grid-template-columns:150px 1fr 1fr;gap:28px;align-items:center;min-height:84px}.aq-footer-main img{width:132px;height:58px;object-fit:contain}.aq-footer-main strong{display:block;color:#fff;font-size:13px}.aq-footer-main span{display:block;margin-top:6px;color:#9bb3bc;font-size:10px;line-height:1.5}.aq-footer-right strong{color:#b9f0e8;text-align:right}.aq-footer-right span{text-align:right}.aq-footer-bottom{margin:18px -7% 0;padding:11px 7%;background:#031b26;color:#8fa9b2;font-size:10px}@media(max-width:700px){.aq-public-footer{padding-left:1rem;padding-right:1rem}.aq-footer-main{grid-template-columns:1fr;gap:12px;padding:8px 0}.aq-footer-right strong,.aq-footer-right span{text-align:left}.aq-footer-bottom{margin-left:-1rem;margin-right:-1rem;padding-left:1rem;padding-right:1rem}}
</style>
""")

render_homepage_header()

st.html("""
<section class="aq-serve-hero">
  <div>
    <div class="aq-kicker">Role-based platform</div>
    <h1>Different responsibilities. One connected operation.</h1>
    <p>AquaLoad gives each person access to the tools relevant to their work, keeping customer ordering separate from authorised warehouse and loading operations.</p>
  </div>
  <aside class="aq-access-note"><div class="aq-kicker">Access approach</div><strong>Right tools, right role.</strong><p>Customer and staff portals are separated so operational controls are only available to authorised users.</p></aside>
</section>
<h2 class="aq-section-title">Designed around real responsibilities</h2>
<p class="aq-section-intro">Each role has a clear place in the seafood fulfilment process, from ordering through loading preparation and operational review.</p>
<div class="aq-roles">
  <div class="aq-role"><div class="aq-role-number">Role 01</div><h3>Customers</h3><p>Browse seafood products, place orders, manage eligible orders and follow the latest order status.</p></div>
  <div class="aq-role"><div class="aq-role-number">Role 02</div><h3>Warehouse administrators</h3><p>Manage customer orders, seafood stock, lorries, insulated box profiles, optimisation plans and operational reports.</p></div>
  <div class="aq-role"><div class="aq-role-number">Role 03</div><h3>Loading supervisors</h3><p>Review the loading arrangement and sequence, then update eligible orders during loading operations.</p></div>
  <div class="aq-role"><div class="aq-role-number">Role 04</div><h3>Seafood suppliers</h3><p>Review relevant loading reports and analytics to understand operational performance and space utilisation.</p></div>
</div>
""")

render_homepage_footer()
