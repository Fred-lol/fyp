"""AquaLoad public homepage. Public pages intentionally ignore portal themes."""
import streamlit as st

from bootstrap import bootstrap_app
from components.public_shell import (
    render_homepage_footer,
    render_homepage_header,
    render_sample_plan,
)


bootstrap_app()
st.set_page_config(
    page_title="AquaLoad | Seafood & Logistics",
    page_icon="AquaLoad.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_homepage_header(active="Home")
st.html(
    '<main class="aq-public-main">'
    '<section class="aq-home-hero"><div class="aq-home-copy">'
    '<div class="aq-public-kicker">Malaysia seafood logistics &middot; smarter loading</div>'
    '<h1>Fresh seafood ordering made simple.<br><span>Smarter loading behind the scenes.</span></h1>'
    '<p>AquaLoad connects seafood customers with a clear wholesale ordering experience and helps operations staff prepare stock, collection and loading in one place.</p>'
    '<a class="aq-public-cta" href="/customer_login" target="_self">Start Ordering &rarr;</a>'
    '</div>'
    f'{render_sample_plan()}</section>'
    '<section class="aq-capabilities" aria-label="AquaLoad capabilities">'
    '<article><div class="aq-public-kicker">01 / Seafood</div><h2>Order seafood</h2>'
    '<p>Browse available products, build a wholesale order and choose a collection point before checkout.</p></article>'
    '<article><div class="aq-public-kicker">02 / Operations</div><h2>Prepare orders</h2>'
    '<p>Coordinate inventory, customer orders, insulated boxes and lorries from the staff portal.</p></article>'
    '<article><div class="aq-public-kicker">03 / Loading</div><h2>Plan loading</h2>'
    '<p>Check lorry weight and space limits, review the loading arrangement and prepare each trip.</p></article>'
    '</section></main>'
)
render_homepage_footer()
