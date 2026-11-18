"""Two clear entry paths into the existing customer and staff workflows."""
import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.public_shell import render_homepage_header, render_homepage_footer

st.set_page_config(page_title="Who We Serve | AquaLoad", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="Who We Serve")
st.html('''<section class="aq-public-intro"><div class="aq-public-kicker">Who We Serve</div>
<h1>Seafood buying and operations, connected.</h1>
<p>AquaLoad gives buyers a straightforward ordering path and staff the tools to prepare each order.</p></section>
<section class="aq-audience-grid">
<article class="aq-audience-card"><div class="aq-public-kicker">For customers</div><h2>Seafood Buyers</h2>
<p>Browse seafood, order by weight, review your orders and track their progress.</p>
<a class="aq-public-cta" href="/customer_login" target="_self">Start Ordering &rarr;</a></article>
<article class="aq-audience-card"><div class="aq-public-kicker">For authorised staff</div><h2>Operations Staff</h2>
<p>Manage inventory, orders, boxes and lorries; review loading plans and reports.</p>
<a class="aq-public-cta" href="/staff_login" target="_self">Staff Entry &rarr;</a></article></section>
<section class="aq-public-section"><div class="aq-public-kicker">How it works</div><h2>From order to loading plan</h2>
<div class="aq-workflow"><span><small>01</small>Order Seafood</span><span><small>02</small>Prepare Orders</span><span><small>03</small>Plan Loading</span></div></section>''')
render_homepage_footer()
