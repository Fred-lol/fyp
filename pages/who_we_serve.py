import sys
from pathlib import Path
import streamlit as st
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.public_shell import render_homepage_header, render_homepage_footer
st.set_page_config(page_title="Who We Serve | AquaLoad", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="Who We Serve")
st.html('<section class="aq-public-intro"><div class="aq-public-kicker">Who We Serve</div><h1>The right workspace for every role.</h1><p>Customer ordering and authorised staff operations work together, with access appropriate to each role.</p></section><article class="aq-public-row"><span>01</span><strong>Customers</strong><p>Browse seafood, choose a collection point, submit a demo order and track its progress.</p></article><article class="aq-public-row"><span>02</span><strong>Warehouse administrators</strong><p>Coordinate stock, orders, lorries, box inventory and loading preparation.</p></article><article class="aq-public-row"><span>03</span><strong>Loading supervisors</strong><p>Review box arrangements and loading sequences before confirming operations.</p></article><article class="aq-public-row"><span>04</span><strong>Seafood suppliers</strong><p>Review relevant loading reports and analytics to understand operational performance.</p></article>')
render_homepage_footer()
