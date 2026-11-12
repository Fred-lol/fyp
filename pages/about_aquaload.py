import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from components.theme import apply_theme
from components.public_shell import render_homepage_footer, render_homepage_header


st.set_page_config(page_title="About AquaLoad", page_icon="A", layout="wide", initial_sidebar_state="collapsed")
apply_theme("Light")

st.html("""
<style>
[data-testid="stSidebar"]{display:none}.aq-public-nav{display:flex;align-items:center;min-height:76px;margin:0 0 34px;padding:0;border-bottom:1px solid #dce9e5;background:rgba(255,255,255,.96)}.aq-logo-link{display:block;width:172px;height:54px}.aq-logo-link img{display:block;width:172px;height:54px;object-fit:contain;image-rendering:auto}
.aq-about-hero{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(250px,.8fr);gap:60px;padding:0 0 44px;border-bottom:1px solid #d7e7e5}.aq-kicker,.aq-small-label,.aq-panel-label{color:#008b91;font-size:11px;font-weight:850;letter-spacing:1.75px;text-transform:uppercase}.aq-about-hero h1{margin:12px 0 17px;color:#073b63;font-size:52px;line-height:1.04;letter-spacing:-2.2px;max-width:730px}.aq-about-hero p{margin:0;color:#587586;font-size:16px;line-height:1.75;max-width:700px}.aq-brief{align-self:end;border-left:3px solid #0a9a9a;padding:4px 0 4px 20px}.aq-brief strong{display:block;margin:8px 0;color:#073b63;font-size:18px}.aq-brief p{font-size:14px;line-height:1.7}
.aq-section-title{margin:46px 0 8px;color:#073b63;font-size:27px;font-weight:800;letter-spacing:-.8px}.aq-section-intro{margin:0 0 26px;color:#607c8a;font-size:14px;line-height:1.7;max-width:700px}.aq-flow{margin:0;border-top:1px solid #dbe8e6}.aq-flow-step{display:grid;grid-template-columns:72px 230px minmax(0,1fr);gap:20px;align-items:start;padding:23px 0;border-bottom:1px solid #dbe8e6}.aq-flow-no{color:#0b9b9b;font-size:12px;font-weight:850;letter-spacing:1px;padding-top:3px}.aq-flow-step strong{color:#073b63;font-size:16px}.aq-flow-step span{color:#66808c;font-size:14px;line-height:1.6}.aq-audience{padding:4px 0 4px 22px;border-left:3px solid #d1e6e3}.aq-audience.is-staff{border-left-color:#0a9a9a}.aq-audience h3{margin:8px 0 10px;color:#073b63;font-size:20px}.aq-audience p{margin:0;color:#5b727c;font-size:14px;line-height:1.75}@media(max-width:800px){.aq-about-hero{grid-template-columns:1fr;gap:26px}.aq-about-hero h1{font-size:39px}.aq-flow-step{grid-template-columns:54px 1fr}.aq-flow-step span{grid-column:2}}@media(max-width:500px){.aq-about-hero h1{font-size:34px}}
.aq-public-footer{box-sizing:border-box;width:100vw;margin:64px 0 -3rem calc(50% - 50vw);padding:24px 7% 0;background:#041e2a}.aq-footer-main{display:grid;grid-template-columns:150px 1fr 1fr;gap:28px;align-items:center;min-height:84px}.aq-footer-main img{width:132px;height:58px;object-fit:contain}.aq-footer-main strong{display:block;color:#fff;font-size:13px}.aq-footer-main span{display:block;margin-top:6px;color:#9bb3bc;font-size:10px;line-height:1.5}.aq-footer-right strong{color:#b9f0e8;text-align:right}.aq-footer-right span{text-align:right}.aq-footer-bottom{margin:18px -7% 0;padding:11px 7%;background:#031b26;color:#8fa9b2;font-size:10px}@media(max-width:700px){.aq-public-footer{padding-left:1rem;padding-right:1rem}.aq-footer-main{grid-template-columns:1fr;gap:12px;padding:8px 0}.aq-footer-right strong,.aq-footer-right span{text-align:left}.aq-footer-bottom{margin-left:-1rem;margin-right:-1rem;padding-left:1rem;padding-right:1rem}}
</style>
""")

render_homepage_header()

st.html("""
<section class="aq-about-hero">
  <div>
    <div class="aq-kicker">Seafood commerce and logistics</div>
    <h1>Built to keep seafood orders and lorry preparation connected.</h1>
    <p>AquaLoad is a role-based platform for a practical seafood workflow: customers order available products while operations staff coordinate stock, insulated boxes and lorry loading preparation.</p>
  </div>
  <aside class="aq-brief"><div class="aq-small-label">The objective</div><strong>Less disconnected work.</strong><p>One shared process from an order being placed to a verified loading plan being prepared.</p></aside>
</section>
<h2 class="aq-section-title">From order to lorry</h2>
<p class="aq-section-intro">AquaLoad brings together the information that would otherwise be handled separately during seafood fulfilment.</p>
<div class="aq-flow">
  <div class="aq-flow-step"><span class="aq-flow-no">01</span><strong>Customer order</strong><span>Available seafood, quantities and customer collection details are recorded in the customer portal.</span></div>
  <div class="aq-flow-step"><span class="aq-flow-no">02</span><strong>Order preparation</strong><span>Staff review the order, update its operational status and prepare suitable insulated box requirements.</span></div>
  <div class="aq-flow-step"><span class="aq-flow-no">03</span><strong>Loading preparation</strong><span>Available lorries and standard box profiles are used to generate a space-conscious loading arrangement.</span></div>
  <div class="aq-flow-step"><span class="aq-flow-no">04</span><strong>Operational visibility</strong><span>Teams can review loading plans, order progress, lorry locations and reports from the staff portal.</span></div>
</div>
""")

st.write("")
left, right = st.columns(2, gap="large")
with left:
    st.html("""<div class="aq-audience"><div class="aq-panel-label">For customers</div><h3>Order with clarity</h3><p>Browse seafood, prepare an order, complete the demo checkout and follow the latest status from one customer account.</p></div>""")
with right:
    st.html("""<div class="aq-audience is-staff"><div class="aq-panel-label">For operations staff</div><h3>Plan with control</h3><p>Manage seafood stock, orders, lorries and box profiles, then prepare loading plans with space and weight checks.</p></div>""")

render_homepage_footer()

