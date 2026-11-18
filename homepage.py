"""Public AquaLoad landing page."""
import streamlit as st
from bootstrap import bootstrap_app
from components.public_shell import render_homepage_header, render_homepage_footer, render_sample_plan

bootstrap_app()
st.set_page_config(page_title="AquaLoad | Seafood & Logistics", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="Home")
st.html('<section class="aq-home-hero"><div><div class="aq-public-kicker">From Kuala Perlis to your business</div><h1>Fresh Seafood.<br>Smarter Loading.</h1><p>Order wholesale seafood with confidence. Keep stock, collection points and lorry loading connected in one practical workspace.</p><a class="aq-public-cta" href="/customer_login" target="_self">Start Ordering &rarr;</a></div>'+render_sample_plan()+'</section>')
st.html("""<section class="aq-capabilities"><article><div class="aq-public-kicker">01 / Seafood</div><h2>Order Seafood</h2><p>Browse available seafood, build your wholesale order and choose a collection point before checkout.</p></article><article><div class="aq-public-kicker">02 / Operations</div><h2>Manage Operations</h2><p>Coordinate inventory, orders, insulated boxes and available lorries from the staff portal.</p></article><article><div class="aq-public-kicker">03 / Loading</div><h2>Plan Loading</h2><p>Check weight and space limits, review the 3D arrangement and prepare each trip with a clear loading sequence.</p></article></section>""")
render_homepage_footer()
