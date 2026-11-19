"""Public introduction to AquaLoad and its seafood operations."""
import sys
from base64 import b64encode
from pathlib import Path
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from components.public_shell import render_homepage_header, render_homepage_footer

st.set_page_config(page_title="About AquaLoad | AquaLoad", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="About AquaLoad")

st.html('''<section class="aq-public-intro"><div class="aq-public-kicker">About AquaLoad</div>
<h1>Rooted in Seafood. Built for Better Operations.</h1>
<p>Based at LKIM Kuala Perlis, AquaLoad brings wholesale seafood ordering and day-to-day loading work into one clear process.</p></section>''')

photo = next((path for path in (
    PROJECT_DIR / "assets" / "lkim.png",
    PROJECT_DIR / "assets" / "kuala_perlis_harbour.jpg",
    PROJECT_DIR / "assets" / "kuala_perlis_harbour.jpeg",
    PROJECT_DIR / "assets" / "kuala_perlis_harbour.png",
) if path.is_file()), None)
if photo:
    kind = "png" if photo.suffix.lower() == ".png" else "jpeg"
    photo_markup = f'<img src="data:image/{kind};base64,{b64encode(photo.read_bytes()).decode()}" alt="Kuala Perlis fishing harbour">'
else:
    photo_markup = '<div class="aq-harbour-unavailable"><div><strong>LKIM Kuala Perlis</strong><br>Our seafood supply base</div></div>'

st.html(f'''<section class="aq-public-section aq-about-business"><div class="aq-harbour-frame">{photo_markup}</div>
<div><div class="aq-public-kicker">Our Business</div><h2>Seafood supply from Kuala Perlis</h2>
<p>Our work starts with seafood and the people who move it. AquaLoad supports clear ordering, stock visibility and practical preparation for each collection or delivery.</p></div></section>''')
st.html('''<section class="aq-public-section"><div class="aq-public-kicker">Why AquaLoad</div>
<h2>One process for a time-sensitive product</h2>
<p>Seafood orders depend on accurate stock, suitable insulated boxes and loading that fits the available lorry space. Keeping those steps together helps staff prepare with fewer manual handoffs.</p></section>
<section class="aq-public-section"><div class="aq-public-kicker">Introducing AquaLoad</div>
<h2>Useful tools for everyday operations</h2>
<p>Customers choose seafood and a collection point. Staff review orders, prepare boxes, plan loads and follow progress through a shared system.</p></section>''')
render_homepage_footer()
