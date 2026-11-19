"""Public paths for seafood customers and AquaLoad operations staff."""
import streamlit as st

from components.public_shell import render_homepage_footer, render_homepage_header


st.set_page_config(page_title="Who We Serve | AquaLoad", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="Who We Serve")
st.html(
    '<main class="aq-public-main">'
    '<section class="aq-public-intro"><div class="aq-public-kicker">Who We Serve</div>'
    '<h1>Seafood buying and operations, connected.</h1>'
    '<p>AquaLoad gives wholesale buyers a clear ordering path and operations staff the tools to prepare each order.</p></section>'
    '<section class="aq-audience-grid">'
    '<article class="aq-audience-card"><div class="aq-public-kicker">For customers</div><h2>Seafood Buyers</h2>'
    '<p>Browse available seafood, order by weight, review order information and follow progress.</p>'
    '<a class="aq-public-cta" href="/customer_login" target="_self">Start Ordering &rarr;</a></article>'
    '<article class="aq-audience-card"><div class="aq-public-kicker">For authorised staff</div><h2>Operations Staff</h2>'
    '<p>Manage inventory, orders, insulated boxes and lorries; prepare loading plans and reports.</p>'
    '<a class="aq-public-cta" href="/staff_login" target="_self">Staff Entry &rarr;</a></article>'
    '</section>'
    '<section class="aq-public-section"><div class="aq-public-kicker">How it works</div>'
    '<h2>From order to loading plan</h2><div class="aq-workflow">'
    '<span><small>01</small>Order Seafood</span><span><small>02</small>Prepare Orders</span>'
    '<span><small>03</small>Plan Loading</span></div></section></main>'
)
render_homepage_footer()
