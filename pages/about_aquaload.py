"""Public overview of AquaLoad and the seafood operation it supports."""
import base64
from pathlib import Path

import streamlit as st

from components.public_shell import PROJECT_DIR, render_homepage_footer, render_homepage_header


st.set_page_config(page_title="About AquaLoad | AquaLoad", page_icon="AquaLoad.png", layout="wide")
render_homepage_header(active="About AquaLoad")

photo = next(
    (path for path in (
        PROJECT_DIR / "assets" / "lkim.png",
        PROJECT_DIR / "assets" / "kuala_perlis_harbour.jpg",
        PROJECT_DIR / "assets" / "kuala_perlis_harbour.jpeg",
        PROJECT_DIR / "assets" / "kuala_perlis_harbour.png",
    ) if path.is_file()),
    None,
)
if photo:
    mime = "image/png" if photo.suffix.lower() == ".png" else "image/jpeg"
    photo_content = base64.b64encode(photo.read_bytes()).decode("ascii")
    photo_markup = f'<img src="data:{mime};base64,{photo_content}" alt="Kuala Perlis fishing harbour and seafood landing area">'
else:
    photo_markup = '<div class="aq-harbour-unavailable">LKIM Kuala Perlis</div>'

st.html(
    '<main class="aq-public-main">'
    '<section class="aq-public-intro"><div class="aq-public-kicker">About AquaLoad</div>'
    '<h1>Rooted in Seafood. Built for Better Operations.</h1>'
    '<p>Based at LKIM Kuala Perlis, AquaLoad brings wholesale seafood ordering and day-to-day loading work into one clear process.</p></section>'
    '<section class="aq-public-section aq-about-business"><div class="aq-harbour-frame">'
    f'{photo_markup}</div><div><div class="aq-public-kicker">Our Business</div>'
    '<h2>Seafood supply from Kuala Perlis</h2>'
    '<p>Our work is rooted in the seafood trade around Kuala Perlis. We are shaping AquaLoad around the practical steps that connect available seafood with wholesale buyers and collection points.</p>'
    '</div></section>'
    '<section class="aq-public-section"><div class="aq-public-kicker">Why AquaLoad</div>'
    '<h2>One process for a time-sensitive product</h2>'
    '<p>Wholesale seafood operations need accurate stock, suitable insulated boxes and loading plans that respect lorry weight and space. Keeping those steps connected makes orders easier to prepare and follow.</p></section>'
    '<section class="aq-public-section"><div class="aq-public-kicker">Introducing AquaLoad</div>'
    '<h2>Useful tools for everyday operations</h2>'
    '<p>Customers choose seafood and a collection point. Staff review orders, manage inventory, plan lorry loads and track operational progress through one system.</p></section>'
    '</main>'
)
render_homepage_footer()
