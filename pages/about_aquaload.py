import sys
from pathlib import Path
import streamlit as st
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.public_shell import render_homepage_header, render_homepage_footer
st.set_page_config(page_title="About AquaLoad | AquaLoad", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="About AquaLoad")
st.html('<section class="aq-public-intro"><div class="aq-public-kicker">About AquaLoad</div><h1>Seafood orders and loading, connected.</h1><p>AquaLoad connects wholesale seafood ordering with practical warehouse and loading preparation, based at LKIM Kuala Perlis.</p></section><article class="aq-public-row"><span>01</span><strong>Order preparation</strong><p>Customers browse available seafood, build a wholesale cart and choose their collection point.</p></article><article class="aq-public-row"><span>02</span><strong>Staff review</strong><p>Staff confirm orders and prepare insulated boxes. Perlis self-pickup orders do not need a lorry.</p></article><article class="aq-public-row"><span>03</span><strong>Loading preparation</strong><p>Check lorry capacity and review a 3D loading plan before confirming the load.</p></article><article class="aq-public-row"><span>04</span><strong>Operational visibility</strong><p>Follow order progress, lorry locations and saved loading reports.</p></article>')
render_homepage_footer()
