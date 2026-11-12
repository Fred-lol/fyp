import base64
from pathlib import Path

import streamlit as st

from bootstrap import bootstrap_app
from components.public_shell import render_homepage_footer, render_homepage_header


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AquaLoad",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

bootstrap_app()


# ============================================================
# STREAMLIT PAGE STYLING
# IMPORTANT:
# Do NOT use "footer { display:none }"
# because it will also hide our AquaLoad footer.
# ============================================================

st.markdown(
    """
    <style>

        html,
        body {
            margin: 0 !important;
            padding: 0 !important;
        }

        .stApp {
            margin: 0 !important;
            padding: 0 !important;
            background: #f7fbfd;
        }

        [data-testid="stAppViewContainer"] {
            background: #f7fbfd;
        }

        [data-testid="stMain"] {
            margin: 0 !important;
            padding: 0 !important;
        }

        [data-testid="stMainBlockContainer"],
        .block-container {
            margin: 0 !important;
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* Hide Streamlit header only */
        header[data-testid="stHeader"] {
            display: none !important;
        }

        /* Hide sidebar */
        [data-testid="stSidebar"] {
            display: none !important;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD LOGO
# AquaLoad.png must be in C:\\fyp
# ============================================================

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "AquaLoad.png"

if not LOGO_PATH.exists():
    st.error(
        "AquaLoad.png cannot be found. "
        "Please place AquaLoad.png in the same folder as homepage.py."
    )
    st.stop()


with open(LOGO_PATH, "rb") as image_file:
    logo_base64 = base64.b64encode(
        image_file.read()
    ).decode("utf-8")


logo_data = f"data:image/png;base64,{logo_base64}"


# ============================================================
# HOMEPAGE HTML + CSS
# ============================================================

html = """
<style>

:root {

    --navy: #062e55;
    --dark-navy: #031c35;

    --malaysia-blue: #003f72;
    --ocean-blue: #087ab0;

    --teal: #009c9a;
    --cyan: #00aeb7;

    --seafoam: #dff7f4;
    --light-cyan: #ebfafa;

    --sand: #f4ead9;
    --gold: #d8a441;
    --coral: #df7055;

    --text: #173b58;
    --muted: #647d90;

    --border: #dceaf0;

    --white: #ffffff;
    --background: #f7fbfd;

}


/* ============================================================
   GLOBAL
============================================================ */

* {
    box-sizing: border-box;
}


html {
    scroll-behavior: smooth;
    overflow-x: hidden;
}


body {

    margin: 0;
    padding: 0;

    overflow-x: hidden;

    font-family:
        Inter,
        "Segoe UI",
        Arial,
        Helvetica,
        sans-serif;

    color: var(--text);

    background: var(--background);

}


.aquaload-page {

    width: 100%;

    margin: 0;
    padding: 0;

    overflow-x: hidden;

}


.aquaload-page a {
    text-decoration: none;
}


/* ============================================================
   NAVIGATION
============================================================ */

.navbar {

    min-height: 92px;

    padding: 0 5.5%;

    display: flex;

    align-items: center;
    justify-content: space-between;

    position: sticky;

    top: 0;

    z-index: 9999;

    background:
        rgba(255,255,255,0.96);

    border-bottom:
        1px solid #e5eef3;

    backdrop-filter: blur(14px);

}


.logo {

    display: flex;
    align-items: center;

}


.logo img {

    width: 205px;
    height: 78px;

    object-fit: contain;

}


.nav-links {

    display: flex;

    align-items: center;

    gap: 34px;

}


.nav-links a {

    position: relative;

    color: #254760;

    font-size: 14px;

    font-weight: 650;

    transition: 0.2s ease;

}


.nav-links a:not(.staff-nav)::after {

    content: "";

    position: absolute;

    left: 0;
    bottom: -8px;

    width: 0;
    height: 2px;

    background: var(--cyan);

    transition: 0.2s ease;

}


.nav-links a:hover {

    color: var(--teal);

}


.nav-links a:hover::after {

    width: 100%;

}


.staff-nav {

    padding: 12px 20px;

    border:
        1px solid #bfdee8;

    border-radius: 11px;

    color:
        var(--navy) !important;

    background: #f0fafc;

}


.staff-nav:hover {

    background: #e3f7f8;

}


/* ============================================================
   HERO
============================================================ */

.hero {

    min-height: 620px;

    padding:
        80px 6.5%
        95px;

    display: grid;

    grid-template-columns:
        1.05fr
        0.95fr;

    align-items: center;

    gap: 55px;

    position: relative;

    overflow: hidden;

    background:

        radial-gradient(
            circle at 12% 20%,
            rgba(0,156,154,0.14),
            transparent 28%
        ),

        radial-gradient(
            circle at 88% 65%,
            rgba(0,63,114,0.11),
            transparent 31%
        ),

        radial-gradient(
            circle at 45% 105%,
            rgba(216,164,65,0.10),
            transparent 27%
        ),

        linear-gradient(
            180deg,
            #fcfeff 0%,
            #edfafa 72%,
            #f6efe4 100%
        );

}


/* ============================================================
   BATIK-INSPIRED PATTERN
============================================================ */

.hero::before {

    content: "";

    position: absolute;

    width: 390px;
    height: 390px;

    left: -150px;
    bottom: -170px;

    opacity: 0.10;

    border-radius: 50%;

    background:

        radial-gradient(
            circle at center,
            transparent 0 13px,
            #009c9a 14px 16px,
            transparent 17px 31px
        );

    background-size:
        68px 68px;

}


.hero::after {

    content: "";

    position: absolute;

    width: 340px;
    height: 340px;

    right: -110px;
    top: -95px;

    opacity: 0.05;

    transform:
        rotate(25deg);

    background:

        repeating-linear-gradient(
            45deg,
            #003f72 0px,
            #003f72 2px,
            transparent 2px,
            transparent 18px
        );

}


.hero-content {

    position: relative;

    z-index: 3;

}


.hero-label {

    display: inline-flex;

    align-items: center;

    gap: 9px;

    margin-bottom: 21px;

    padding: 8px 15px;

    border:
        1px solid #cfe9e8;

    border-radius: 30px;

    color: #007d86;

    background:
        rgba(255,255,255,0.72);

    font-size: 11px;

    font-weight: 750;

}


.label-dot {

    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: var(--teal);

    box-shadow:
        0 0 0 4px
        rgba(0,156,154,0.10);

}


.hero h1 {

    max-width: 760px;

    margin:
        0 0 22px;

    color: #092f55;

    font-size: 55px;

    line-height: 1.07;

    letter-spacing:
        -2.2px;

}


.hero h1 span {

    display: block;

    margin-top: 7px;

    color: var(--teal);

}


.hero-description {

    max-width: 690px;

    margin: 0;

    color: #60798c;

    font-size: 16px;

    line-height: 1.8;

}


/* ============================================================
   SEAFOOD TAGS
============================================================ */

.local-tags {

    display: flex;

    flex-wrap: wrap;

    gap: 9px;

    margin-top: 21px;

}


.local-tags span {

    padding: 7px 12px;

    border:
        1px solid #d5e9e8;

    border-radius: 30px;

    color: #557485;

    background:
        rgba(255,255,255,0.75);

    font-size: 10px;

    font-weight: 650;

}


/* ============================================================
   HERO BUTTONS
============================================================ */

.hero-buttons {

    display: flex;

    flex-wrap: wrap;

    gap: 13px;

    margin-top: 33px;

}


.primary-button,
.secondary-button {

    display: inline-flex;

    align-items: center;
    justify-content: center;

    min-width: 165px;

    padding: 14px 22px;

    border-radius: 11px;

    font-size: 13px;

    font-weight: 750;

    transition: 0.2s ease;

}


.primary-button {

    color: white;

    background:

        linear-gradient(
            135deg,
            #066b9e,
            #00a6ad
        );

    box-shadow:

        0 10px 28px
        rgba(0,130,155,0.16);

}


.primary-button:hover {

    transform:
        translateY(-2px);

}


.secondary-button {

    color: var(--navy);

    border:
        1px solid #badbe6;

    background:
        rgba(255,255,255,0.85);

}


.secondary-button:hover {

    transform:
        translateY(-2px);

    background: white;

}


/* ============================================================
   OPTIMIZATION PREVIEW
============================================================ */

.hero-visual {

    position: relative;

    z-index: 3;

    display: flex;

    align-items: center;
    justify-content: center;

}


.visual-panel {

    width: 100%;

    max-width: 530px;

    padding: 26px;

    border-radius: 25px;

    color: white;

    background:

        radial-gradient(
            circle at 85% 10%,
            rgba(0,174,183,0.17),
            transparent 32%
        ),

        linear-gradient(
            145deg,
            #062f55,
            #064c68
        );

    box-shadow:

        0 30px 70px
        rgba(7,47,79,0.20);

}


.visual-header {

    display: flex;

    justify-content: space-between;
    align-items: center;

    margin-bottom: 22px;

}


.visual-title {

    font-size: 14px;

    font-weight: 700;

}


.status {

    padding: 5px 10px;

    border-radius: 30px;

    color: #91f3e9;

    background:
        rgba(255,255,255,0.08);

    font-size: 9px;

    font-weight: 700;

}


/* ============================================================
   CARGO SPACE
============================================================ */

.lorry {

    position: relative;

    height: 260px;

    overflow: hidden;

    border:
        1px solid
        rgba(255,255,255,0.13);

    border-radius: 16px;

    background: #041d31;

}


.lorry::before {

    content: "";

    position: absolute;

    inset: 0;

    background-image:

        linear-gradient(
            rgba(255,255,255,0.04)
            1px,
            transparent 1px
        ),

        linear-gradient(
            90deg,
            rgba(255,255,255,0.04)
            1px,
            transparent 1px
        );

    background-size:
        24px 24px;

}


.cargo-label {

    position: absolute;

    top: 12px;
    left: 15px;

    z-index: 3;

    color: #7f9cad;

    font-size: 9px;

    letter-spacing: 1px;

    text-transform: uppercase;

}


.box {

    position: absolute;

    z-index: 2;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 7px;

    color: white;

    font-size: 9px;

    font-weight: 700;

}


.box-teal {

    background:

        linear-gradient(
            135deg,
            #18b9b0,
            #087d82
        );

}


.box-blue {

    background:

        linear-gradient(
            135deg,
            #258fd0,
            #075b94
        );

}


.box-orange {

    background:

        linear-gradient(
            135deg,
            #e49755,
            #b75b32
        );

}


.box1 {

    width: 29%;
    height: 66px;

    left: 8%;
    bottom: 25px;

}


.box2 {

    width: 29%;
    height: 59px;

    left: 8%;
    bottom: 96px;

}


.box3 {

    width: 25%;
    height: 84px;

    left: 40%;
    bottom: 25px;

}


.box4 {

    width: 25%;
    height: 54px;

    left: 40%;
    bottom: 114px;

}


.box5 {

    width: 24%;
    height: 65px;

    right: 8%;
    bottom: 25px;

}


.box6 {

    width: 24%;
    height: 77px;

    right: 8%;
    bottom: 95px;

}


/* ============================================================
   OPTIMIZATION STATS
============================================================ */

.visual-stats {

    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 10px;

    margin-top: 14px;

}


.visual-stat {

    padding: 11px;

    border-radius: 10px;

    background:
        rgba(255,255,255,0.07);

}


.visual-stat span {

    display: block;

    color: #9db7c6;

    font-size: 8px;

}


.visual-stat strong {

    display: block;

    margin-top: 4px;

    color: #9dfbef;

    font-size: 10px;

}


/* ============================================================
   WAVE DIVIDER
============================================================ */

.sea-wave {

    height: 55px;

    background:

        radial-gradient(
            circle at 30px -3px,

            transparent 29px,

            #dff7f4 30px,

            #dff7f4 35px,

            transparent 36px
        );

    background-size:
        76px 62px;

    opacity: 0.72;

}


/* ============================================================
   CUSTOMER / STAFF SECTION
============================================================ */

.portal-section {

    padding:
        75px 6%
        105px;

    background: white;

}


.section-header {

    max-width: 780px;

    margin:
        0 auto 50px;

    text-align: center;

}


.section-label {

    color: var(--teal);

    font-size: 10px;

    font-weight: 800;

    letter-spacing:
        1.6px;

    text-transform: uppercase;

}


.section-header h2 {

    margin:
        11px 0 13px;

    color: #113c5b;

    font-size: 36px;

    line-height: 1.2;

}


.section-header p {

    margin: 0;

    color: #718596;

    font-size: 14px;

    line-height: 1.75;

}


.portal-grid {

    max-width: 1150px;

    margin: auto;

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 28px;

}


.portal-card {

    min-height: 460px;

    padding: 38px;

    border-radius: 25px;

    transition: 0.25s ease;

}


.portal-card:hover {

    transform:
        translateY(-5px);

}


/* ============================================================
   CUSTOMER CARD
============================================================ */

.customer-card {

    border:
        1px solid #cce8eb;

    background:

        radial-gradient(
            circle at 95% 0,
            rgba(0,174,183,0.13),
            transparent 28%
        ),

        radial-gradient(
            circle at 5% 100%,
            rgba(216,164,65,0.10),
            transparent 28%
        ),

        linear-gradient(
            145deg,
            #fbffff,
            #eaf9f7
        );

}


.customer-card:hover {

    box-shadow:

        0 20px 45px
        rgba(0,120,140,0.10);

}


/* ============================================================
   STAFF CARD
============================================================ */

.staff-card {

    color: white;

    background:

        radial-gradient(
            circle at 90% 10%,
            rgba(0,174,183,0.17),
            transparent 30%
        ),

        linear-gradient(
            145deg,
            #082f54,
            #041e37
        );

}


.staff-card:hover {

    box-shadow:

        0 20px 50px
        rgba(4,34,60,0.22);

}


.portal-icon {

    width: 62px;
    height: 62px;

    display: flex;

    align-items: center;
    justify-content: center;

    margin-bottom: 20px;

    border-radius: 18px;

    font-size: 29px;

}


.customer-card
.portal-icon {

    background: white;

}


.staff-card
.portal-icon {

    background:
        rgba(255,255,255,0.08);

}


.portal-type {

    display: inline-block;

    margin-bottom: 16px;

    padding: 6px 10px;

    border-radius: 30px;

    font-size: 9px;

    font-weight: 800;

    letter-spacing: 1.2px;

    text-transform: uppercase;

}


.customer-card
.portal-type {

    color: #008b94;

    background: white;

}


.staff-card
.portal-type {

    color: #8eece5;

    background:
        rgba(255,255,255,0.08);

}


.portal-card h3 {

    margin:
        0 0 13px;

    font-size: 29px;

}


.customer-card h3 {

    color: #103b59;

}


.portal-description {

    min-height: 78px;

    margin:
        0 0 24px;

    font-size: 13px;

    line-height: 1.72;

}


.customer-card
.portal-description {

    color: #617d90;

}


.staff-card
.portal-description {

    color: #a9bdca;

}


.portal-features {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 12px;

    margin-bottom: 31px;

}


.portal-feature {

    display: flex;

    align-items: center;

    gap: 9px;

    font-size: 11px;

}


.check {

    width: 18px;
    height: 18px;

    display: flex;

    align-items: center;
    justify-content: center;

    flex: 0 0 18px;

    border-radius: 50%;

    font-size: 9px;

}


.customer-card
.check {

    color: #008e96;

    background: #dff5f4;

}


.staff-card
.check {

    color: #8df4e9;

    background:
        rgba(255,255,255,0.08);

}


.portal-actions {

    display: flex;

    align-items: center;

    flex-wrap: wrap;

    gap: 14px;

}


.portal-button {

    display: inline-flex;

    align-items: center;
    justify-content: center;

    padding: 13px 21px;

    border-radius: 10px;

    font-size: 12px;

    font-weight: 750;

    transition: 0.2s ease;

}


.portal-button:hover {

    transform:
        translateY(-2px);

}


.customer-button {

    color: white;

    background:

        linear-gradient(
            135deg,
            #0776a7,
            #00aab4
        );

}


.staff-button {

    color: #052d51;

    background: #9cf2eb;

}


.portal-secondary {

    font-size: 11px;

    font-weight: 600;

}


.customer-card
.portal-secondary {

    color: #47788f;

}


.staff-card
.portal-secondary {

    color: #a8c7d4;

}


/* ============================================================
   WHO WE SERVE
============================================================ */

.users {

    padding:
        95px 6%;

    position: relative;

    background:

        linear-gradient(
            180deg,
            #f4f9fb,
            #edf7f6
        );

}


.users-grid {

    max-width: 1150px;

    margin: auto;

    display: grid;

    grid-template-columns:
        repeat(4,1fr);

    gap: 17px;

}


.user-card {

    min-height: 220px;

    padding: 26px;

    border:
        1px solid #dce9ed;

    border-radius: 18px;

    background:
        rgba(255,255,255,0.92);

    transition: 0.2s ease;

}


.user-card:hover {

    transform:
        translateY(-4px);

    box-shadow:

        0 15px 30px
        rgba(12,64,85,0.07);

}


.user-icon {

    width: 46px;
    height: 46px;

    display: flex;

    align-items: center;
    justify-content: center;

    margin-bottom: 18px;

    border-radius: 13px;

    background: #e4f6f5;

    font-size: 21px;

}


.user-card h4 {

    margin:
        0 0 9px;

    color: #173e5c;

    font-size: 14px;

}


.user-card p {

    margin: 0;

    color: #728797;

    font-size: 11px;

    line-height: 1.7;

}


/* ============================================================
   ABOUT AQUALOAD
============================================================ */

.about {

    padding:
        100px 7%;

    position: relative;

    overflow: hidden;

    color: white;

    background:

        radial-gradient(
            circle at 90% 20%,
            rgba(0,174,183,0.15),
            transparent 30%
        ),

        linear-gradient(
            135deg,
            #052a4a,
            #07516d
        );

}


.about::before {

    content: "";

    position: absolute;

    width: 340px;
    height: 340px;

    left: -130px;
    bottom: -180px;

    border:
        35px solid
        rgba(216,164,65,0.08);

    border-radius: 50%;

}


.about-grid {

    max-width: 1100px;

    margin: auto;

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 70px;

    align-items: center;

    position: relative;

    z-index: 2;

}


.about-label {

    color: #8cece5;

    font-size: 9px;

    font-weight: 800;

    letter-spacing: 1.6px;

}


.about h2 {

    margin:
        13px 0 17px;

    font-size: 38px;

    line-height: 1.18;

}


.about p {

    margin: 0;

    color: #b0c5d1;

    font-size: 13px;

    line-height: 1.85;

}


.about-list {

    display: grid;

    gap: 11px;

}


.about-item {

    padding: 15px 18px;

    border:
        1px solid
        rgba(255,255,255,0.09);

    border-radius: 11px;

    color: #ccdae3;

    background:
        rgba(255,255,255,0.04);

    font-size: 11px;

}


/* ============================================================
   MALAYSIA COLOUR STRIP
============================================================ */

.malaysia-strip {

    height: 5px;

    background:

        linear-gradient(
            90deg,

            #003f72 0%,
            #003f72 25%,

            #00aeb7 25%,
            #00aeb7 50%,

            #d8a441 50%,
            #d8a441 75%,

            #df7055 75%,
            #df7055 100%
        );

}


/* ============================================================
   AQUALOAD FOOTER
   IMPORTANT:
   This is NOT hidden anymore.
============================================================ */

.aquaload-footer {

    min-height: 145px;

    padding:
        28px 6%;

    display: grid;

    grid-template-columns:
        auto 1fr auto;

    align-items: center;

    gap: 35px;

    background: #031a2e;

    color: #8197a7;

}


.footer-logo img {

    width: 160px;
    height: 70px;

    object-fit: contain;

}


.footer-center {

    text-align: center;

}


.footer-center strong {

    display: block;

    margin-bottom: 5px;

    color: #c7d8e2;

    font-size: 12px;

}


.footer-center span {

    color: #7892a3;

    font-size: 10px;

}


.footer-right {

    text-align: right;

}


.footer-right strong {

    display: block;

    color: #8cece5;

    font-size: 11px;

}


.footer-right span {

    display: block;

    margin-top: 4px;

    color: #6f8797;

    font-size: 9px;

}


.footer-bottom {

    padding:
        13px 6%;

    border-top:
        1px solid
        rgba(255,255,255,0.05);

    text-align: center;

    color: #5f7686;

    background: #031a2e;

    font-size: 9px;

}


/* ============================================================
   RESPONSIVE
============================================================ */

@media(max-width: 1000px) {

    .hero {

        grid-template-columns: 1fr;

    }


    .hero h1 {

        font-size: 47px;

    }


    .hero-visual {

        max-width: 650px;

        margin: auto;

        width: 100%;

    }


    .portal-grid {

        grid-template-columns: 1fr;

    }


    .users-grid {

        grid-template-columns:
            1fr 1fr;

    }


    .about-grid {

        grid-template-columns: 1fr;

    }

}


@media(max-width: 760px) {

    .navbar {

        min-height: 78px;

    }


    .logo img {

        width: 155px;
        height: 65px;

    }


    .nav-links {

        gap: 10px;

    }


    .nav-links a:not(.staff-nav) {

        display: none;

    }


    .staff-nav {

        padding:
            10px 14px;

        font-size: 12px;

    }


    .hero {

        padding:
            60px 5%
            75px;

    }


    .hero h1 {

        font-size: 38px;

        letter-spacing: -1.5px;

    }


    .hero-description {

        font-size: 14px;

    }


    .section-header h2 {

        font-size: 30px;

    }


    .portal-features {

        grid-template-columns: 1fr;

    }


    .users-grid {

        grid-template-columns: 1fr;

    }


    .visual-stats {

        grid-template-columns: 1fr;

    }


    .about h2 {

        font-size: 31px;

    }


    .aquaload-footer {

        grid-template-columns: 1fr;

        text-align: center;

    }


    .footer-logo img {

        margin: auto;

    }


    .footer-right {

        text-align: center;

    }

}

/* ============================================================
   2026 HOMEPAGE REFINEMENT
   Keeps the existing page structure and links, while giving the
   product a more editorial, seafood-logistics identity.
============================================================ */

:root {
    --ink: #082b3b;
    --ink-soft: #244858;
    --ocean: #0b746f;
    --foam: #e9f4f1;
    --sand: #f6f3ed;
}

.aquaload-page {
    color: var(--ink);
    background: #ffffff;
}

.navbar {
    min-height: 76px;
    padding: 0 7%;
    border-bottom: 1px solid #dce9e5;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: none;
}

.logo img { width: 172px; max-height: 54px; object-fit: contain; }
.nav-links { gap: 27px; }
.nav-links a { color: #3b5965; font-size: 12px; font-weight: 700; letter-spacing: .01em; }
.nav-links a:hover { color: var(--ocean); }
.staff-nav {
    padding: 11px 18px !important;
    border: 1px solid var(--ink) !important;
    border-radius: 5px;
    color: #ffffff !important;
    background: var(--ink) !important;
    box-shadow: 0 2px 0 rgba(0,0,0,.08);
}
.staff-nav:hover { color: #ffffff !important; border-color: var(--ocean) !important; background: var(--ocean) !important; }

.hero {
    min-height: 650px;
    padding: 104px 7% 96px;
    display: grid;
    grid-template-columns: minmax(0, 1.12fr) minmax(360px, .88fr);
    gap: 72px;
    align-items: center;
    background: linear-gradient(115deg, #f8fbfa 0%, #f8fbfa 59%, #e9f2ef 59%, #e9f2ef 100%);
}

.hero::before { inset: auto 0 0 auto; width: 50%; height: 100%; opacity: .45; background: linear-gradient(135deg, transparent 0 45%, rgba(11, 116, 111, .08) 45% 46%, transparent 46% 100%); }
.hero::after { display: none; }
.hero-content, .hero-visual { position: relative; z-index: 2; }
.hero-label { margin-bottom: 22px; padding: 7px 10px; border: 0; border-left: 3px solid var(--ocean); border-radius: 0; background: transparent; color: var(--ocean); font-size: 10px; letter-spacing: .14em; text-transform: uppercase; }
.label-dot { display: none; }
.hero h1 { max-width: 700px; color: var(--ink); font-size: clamp(43px, 4.7vw, 67px); line-height: 1.02; letter-spacing: -2.8px; }
.hero h1 span { margin-top: 11px; color: var(--ocean); }
.hero-description { max-width: 620px; color: #59717c; font-size: 16px; line-height: 1.75; }
.local-tags { gap: 8px; margin: 27px 0 31px; }
.local-tags span {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border: 1px solid #cfe1dc;
    border-radius: 4px;
    padding: 8px 10px;
    color: #315865;
    background: rgba(255,255,255,.65);
    font-size: 10px;
    font-weight: 700;
}
.local-tags span::before {
    content: "";
    display: inline-block;
    width: 13px;
    height: 13px;
    flex: 0 0 13px;
    background: var(--ocean);
    -webkit-mask: center / contain no-repeat;
    mask: center / contain no-repeat;
}
.local-tags span:nth-child(1)::before { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/fish.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/fish.svg"); }
.local-tags span:nth-child(2)::before { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/map-pin.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/map-pin.svg"); }
.local-tags span:nth-child(3)::before { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/truck.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/truck.svg"); }
.local-tags span:nth-child(4)::before { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/boxes.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/boxes.svg"); }
.hero-buttons { gap: 12px; }
.primary-button, .secondary-button { border-radius: 5px; padding: 14px 20px; font-size: 12px; }
.primary-button { color: #ffffff; background: var(--ink); box-shadow: none; }
.primary-button:hover { background: var(--ocean); }
.secondary-button { border-color: var(--ocean); color: var(--ocean); background: #ffffff; }

.visual-panel {
    max-width: 600px;
    padding: 26px;
    border: 1px solid #126784;
    border-radius: 10px;
    color: #ffffff;
    background: linear-gradient(145deg, #064267, #063457);
    box-shadow: 0 20px 42px rgba(8,43,59,.20);
}
.visual-header { margin-bottom: 18px; padding-bottom: 16px; border-bottom: 1px solid rgba(183,231,229,.24); }
.visual-title { color: #ffffff; font-size: 15px; font-weight: 800; letter-spacing: .01em; }
.status { padding: 7px 11px; border: 1px solid rgba(136,239,227,.38); border-radius: 4px; color: #bffff7; background: rgba(4,139,164,.28); font-size: 9px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.lorry {
    height: 265px;
    isolation: isolate;
    border: 1px solid #277c99;
    border-radius: 6px;
    background-color: #042b47;
    background-image: linear-gradient(rgba(129,188,204,.10) 1px, transparent 1px), linear-gradient(90deg, rgba(129,188,204,.10) 1px, transparent 1px);
    background-size: 20px 20px;
}
.lorry::before {
    display: none;
}
.lorry::after {
    display: none;
}
.cargo-label { top: 15px; left: 16px; color: #b8e8eb; font-size: 9px; font-weight: 800; letter-spacing: .12em; }
.box { border: 1px solid rgba(255,255,255,.30); border-radius: 5px; color: #ffffff; font-size: 11px; font-weight: 800; box-shadow: 0 6px 14px rgba(0,0,0,.15); transform: none; }
.box::after { display:none; }
.box-teal { background: #0e9895; }
.box-blue { background: #1877b5; }
.box-orange { background: #c8753b; }
.box1, .box2 { left: 8%; width: 28%; }
.box3, .box4 { left: 39%; width: 26%; }
.box5, .box6 { right: 8%; width: 24%; }
.box1, .box3, .box5 { bottom: 42px; }
.box2, .box4, .box6 { bottom: 114px; }
.box1, .box2 { height:64px; }.box3, .box4 { height:64px; }.box5, .box6 { height:64px; }
.sample-plan-ends { position:absolute; z-index:4; left:8%; right:8%; bottom:8px; display:flex; justify-content:space-between; pointer-events:none; }
.sample-plan-ends span { padding:5px 7px; border-radius:4px; font-size:8px; font-weight:800; letter-spacing:.05em; text-transform:uppercase; box-shadow:0 2px 7px rgba(0,0,0,.22); }
.sample-plan-ends .gate { color:#331804; background:#ffa24d; }.sample-plan-ends .deep { color:#032633; background:#67e6e1; }
.visual-stats { gap: 10px; margin-top: 14px; }
.visual-stat { padding: 12px; border: 1px solid rgba(183,231,229,.18); border-radius: 6px; background: rgba(255,255,255,.07); }
.visual-stat span { color: #b7d1db; font-size: 9px; }
.visual-stat strong { margin-top: 5px; color: #a9f4eb; font-size: 12px; }
.sea-wave { height: 20px; opacity: .42; }

.portal-section { padding: 96px 7%; }
.section-header { max-width: 690px; margin-bottom: 48px; }
.section-label { color: var(--ocean); font-size: 10px; letter-spacing: .16em; }
.section-header h2 { color: var(--ink); font-size: clamp(31px, 3vw, 42px); letter-spacing: -1.2px; }
.portal-grid { gap: 20px; }
.portal-card { min-height: 430px; padding: 36px; border-radius: 8px; }
.customer-card { border-color: #cfe3de; background: linear-gradient(145deg, #fbfdfc, #edf6f3); }
.staff-card { background: linear-gradient(145deg, #082b3b, #0a4655); }
.portal-icon, .user-icon { border-radius: 5px; font-size: 0; }
/* Lucide is an open-source SVG icon set, loaded from its public CDN. */
.portal-icon::after, .user-icon::after {
    content: "";
    display: block;
    width: 23px;
    height: 23px;
    background: var(--ocean);
    -webkit-mask: center / contain no-repeat;
    mask: center / contain no-repeat;
}
.portal-card:nth-child(1) .portal-icon::after {
    -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/fish.svg");
    mask-image: url("https://unpkg.com/lucide-static@latest/icons/fish.svg");
}
.portal-card:nth-child(2) .portal-icon::after {
    background: #b9f0e8;
    -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/truck.svg");
    mask-image: url("https://unpkg.com/lucide-static@latest/icons/truck.svg");
}
.portal-type { border-radius: 3px; }
.portal-button { border-radius: 5px; }
.customer-button { background: var(--ocean); }
.staff-button { background: #b9f0e8; }

.users { padding: 92px 7%; background: var(--sand); }
.users-grid { gap: 14px; }
.user-card { min-height: 210px; padding: 25px; border-radius: 7px; border-color: #e0e8e4; background: #fff; }
.user-card:nth-child(1) .user-icon::after { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/user-round.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/user-round.svg"); }
.user-card:nth-child(2) .user-icon::after { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/warehouse.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/warehouse.svg"); }
.user-card:nth-child(3) .user-icon::after { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/package.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/package.svg"); }
.user-card:nth-child(4) .user-icon::after { -webkit-mask-image: url("https://unpkg.com/lucide-static@latest/icons/bar-chart-3.svg"); mask-image: url("https://unpkg.com/lucide-static@latest/icons/bar-chart-3.svg"); }
.user-icon { width: 40px; height: 40px; margin-bottom: 17px; background: var(--foam); }
.user-icon::after { color: var(--ocean); }
.user-card h4 { color: var(--ink); font-size: 14px; }

.about { padding: 104px 7%; background: linear-gradient(130deg, #062937, #0c5360); }
.about::before { border-radius: 0; transform: rotate(45deg); }
.about h2 { font-size: clamp(32px, 3.3vw, 45px); letter-spacing: -1.3px; }
.about-item { position: relative; padding: 17px 20px 17px 42px; border-radius: 5px; }
.about-item::before { content: ""; position: absolute; top: 23px; left: 20px; width: 7px; height: 7px; background: #8ee8de; }

.aquaload-footer {
    min-height: 104px;
    padding: 20px 7%;
    gap: 28px;
    background: #041e2a;
}
.footer-logo img { width: 132px; height: 58px; }
.footer-center strong { color: #ffffff; font-size: 13px; }
.footer-center span { color: #9bb3bc; font-size: 10px; }
.footer-right strong { color: #b9f0e8; font-size: 11px; }
.footer-right span { color: #9bb3bc; font-size: 10px; }
.footer-bottom {
    padding: 11px 7%;
    color: #8fa9b2;
    background: #031b26;
    font-size: 10px;
}

/* Keep the landing page focused. Detailed content has dedicated pages. */
.sea-wave, .portal-section, .users, .about { display: none; }

@media (max-width: 880px) {
    .hero { grid-template-columns: 1fr; gap: 45px; padding-top: 80px; }
    .hero-visual { max-width: 620px; width: 100%; }
}

</style>


<div class="aquaload-page">


<!-- ============================================================
     NAVIGATION
============================================================ -->

<nav class="navbar">


    <a
        class="logo"
        href="/"
    >

        <img
            src="AQUALOAD_LOGO"
            alt="AquaLoad Logo"
        >

    </a>


    <div class="nav-links">


        <a href="/">
            Home
        </a>

        <a href="/about_aquaload">
            About AquaLoad
        </a>


        <a href="/who_we_serve">
            Who We Serve
        </a>


        <a
            href="/staff_login"
            target="_self"
            class="staff-nav"
        >
            Staff Entry
        </a>


    </div>


</nav>



<!-- ============================================================
     HERO
============================================================ -->

<section
    class="hero"
    id="home"
>


    <div class="hero-content">


        <div class="hero-label">


            <span class="label-dot"></span>


            Malaysia Seafood Logistics · Smarter Loading


        </div>


        <h1>


            Fresh seafood ordering
            made simple.


            <span>

                Smarter loading
                behind the scenes.

            </span>


        </h1>


        <p class="hero-description">


            AquaLoad connects seafood customers with a
            convenient online ordering experience while
            providing seafood suppliers and warehouse
            staff with intelligent tools for managing
            orders, insulated fish storage boxes and
            optimized lorry loading.


        </p>


        <div class="local-tags">


            <span>
                Fresh seafood
            </span>


            <span>
                Malaysian supply
            </span>


            <span>
                Smart logistics
            </span>


            <span>
                Space optimization
            </span>


        </div>


        <div class="hero-buttons">


            <a
                href="/customer_login"
                class="primary-button"
            >

                Start Ordering

            </a>

        </div>


    </div>



    <!-- ========================================================
         LOADING OPTIMIZATION PREVIEW
    ========================================================= -->

    <div class="hero-visual">


        <div class="visual-panel">


            <div class="visual-header">


                <div class="visual-title">

                    Sample loading plan

                </div>


                <div class="status">

                    Sample only

                </div>


            </div>


            <div class="lorry">


                <div class="cargo-label">

                    Insulated box arrangement · 6 positions

                </div>


                <div class="sample-plan-ends" aria-hidden="true">

                    <span class="gate">Rear loading gate</span>

                    <span class="deep">Deepest end</span>

                </div>


                <div class="box box-teal box1">

                    20L

                </div>


                <div class="box box-teal box2">

                    20L

                </div>


                <div class="box box-blue box3">

                    50L

                </div>


                <div class="box box-blue box4">

                    50L

                </div>


                <div class="box box-orange box5">

                    75L

                </div>


                <div class="box box-orange box6">

                    75L

                </div>


            </div>


            <div class="visual-stats">


                <div class="visual-stat">

                    <span>
                        Box positions
                    </span>

                    <strong>
                        6 ready
                    </strong>

                </div>


                <div class="visual-stat">

                    <span>
                        Weight capacity used
                    </span>

                    <strong>
                        68%
                    </strong>

                </div>


                <div class="visual-stat">

                    <span>
                        Plan validation
                    </span>

                    <strong>
                        Valid
                    </strong>

                </div>


            </div>


        </div>


    </div>


</section>



<!-- ============================================================
     WAVE
============================================================ -->

<div class="sea-wave"></div>



<!-- ============================================================
     CUSTOMER / STAFF
============================================================ -->

<section
    class="portal-section"
    id="shop"
>


    <div class="section-header">


        <div class="section-label">

            Choose Your AquaLoad Experience

        </div>


        <h2>

            Seafood shopping for customers.
            Smart operations for staff.

        </h2>


        <p>

            AquaLoad keeps seafood ordering separate
            from warehouse and loading operations so
            customers can shop without being confused
            by technical logistics functions.

        </p>


    </div>


    <div class="portal-grid">



        <!-- CUSTOMER -->

        <div
            class="
                portal-card
                customer-card
            "
        >


            <div class="portal-icon">

                🐟

            </div>


            <div class="portal-type">

                For Seafood Customers

            </div>


            <h3>

                Shop Fresh Seafood

            </h3>


            <p class="portal-description">

                Browse available seafood products,
                place an order online and monitor
                the latest status of your seafood
                order through a simple customer
                experience.

            </p>


            <div class="portal-features">


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Browse Seafood

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Place Seafood Order

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    View My Orders

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Update / Cancel Order

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Track Order Status

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Manage Profile

                </div>


            </div>


            <div class="portal-actions">


                <a
                    href="/customer_login"
                    target="_self"
                    class="
                        portal-button
                        customer-button
                    "
                >

                    Start Ordering →

                </a>


                <span class="portal-secondary">

                    Customer Login / Register

                </span>


            </div>


        </div>



        <!-- STAFF -->

        <div
            class="
                portal-card
                staff-card
            "
            id="staff"
        >


            <div class="portal-icon">

                🚚

            </div>


            <div class="portal-type">

                Business Operations

            </div>


            <h3>

                AquaLoad Operations

            </h3>


            <p class="portal-description">

                A dedicated operational portal for
                Warehouse Administrators, Loading
                Supervisors and Seafood Suppliers
                to manage loading resources and
                prepare optimized lorry loading plans.

            </p>


            <div class="portal-features">


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Manage Customer Orders

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Lorry Profiles

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Storage Box Profiles

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Space Optimization

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    3D Loading Plan

                </div>


                <div class="portal-feature">

                    <span class="check">✓</span>

                    Reports & Analytics

                </div>


            </div>


            <div class="portal-actions">


                <a
                    href="/staff_login"
                    target="_self"
                    class="
                        portal-button
                        staff-button
                    "
                >

                    Enter Staff Portal →

                </a>


                <span class="portal-secondary">

                    Authorized Staff Only

                </span>


            </div>


        </div>


    </div>


</section>



<!-- ============================================================
     WHO WE SERVE
============================================================ -->

<section
    class="users"
    id="users"
>


    <div class="section-header">


        <div class="section-label">

            Who AquaLoad Serves

        </div>


        <h2>

            Designed around each user's responsibilities

        </h2>


        <p>

            Different users access different functions
            so the system remains simple, organized
            and suitable for each role.

        </p>


    </div>


    <div class="users-grid">


        <div class="user-card">


            <div class="user-icon">

                🐟

            </div>


            <h4>

                Customer

            </h4>


            <p>

                Browse seafood products, place orders,
                manage personal orders and track the
                latest order status.

            </p>


        </div>


        <div class="user-card">


            <div class="user-icon">

                🏭

            </div>


            <h4>

                Warehouse Administrator

            </h4>


            <p>

                Manage customer orders, user accounts,
                lorries, insulated box profiles,
                optimized loading plans and reports.

            </p>


        </div>


        <div class="user-card">


            <div class="user-icon">

                📦

            </div>


            <h4>

                Loading Supervisor

            </h4>


            <p>

                Review the 3D loading arrangement
                and loading sequence and mark
                eligible orders as loaded.

            </p>


        </div>


        <div class="user-card">


            <div class="user-icon">

                📊

            </div>


            <h4>

                Seafood Supplier

            </h4>


            <p>

                Review loading reports and operational
                analytics to understand loading
                performance and space utilization.

            </p>


        </div>


    </div>


</section>



<!-- ============================================================
     ABOUT
============================================================ -->

<section
    class="about"
    id="about"
>


    <div class="about-grid">


        <div>


            <div class="about-label">

                ABOUT AQUALOAD

            </div>


            <h2>

                Malaysian seafood commerce supported
                by smarter loading operations.

            </h2>


            <p>

                AquaLoad is an integrated seafood
                ordering and lorry space optimization
                platform.

                Customers can conveniently order
                seafood online, while the operational
                side helps seafood suppliers and
                warehouse personnel organize confirmed
                orders and generate efficient
                arrangements for insulated fish storage
                boxes inside lorries.

                By connecting ordering information
                with loading preparation, AquaLoad
                provides a clearer workflow from
                seafood order management to lorry
                loading.

            </p>


        </div>


        <div class="about-list">


            <div class="about-item">

                🐟 Online seafood ordering for customers

            </div>


            <div class="about-item">

                📋 Customer order and status management

            </div>


            <div class="about-item">

                🚚 Lorry profile management

            </div>


            <div class="about-item">

                📦 Insulated fish storage box management

            </div>


            <div class="about-item">

                ⚙ Intelligent 3D space optimization

            </div>


            <div class="about-item">

                ◈ 3D loading plan visualization

            </div>


            <div class="about-item">

                📊 Loading reports and analytics

            </div>


        </div>


    </div>


</section>



<!-- ============================================================
     COLOUR STRIP
============================================================ -->

<div class="malaysia-strip"></div>



<!-- ============================================================
     REAL AQUALOAD FOOTER
============================================================ -->

<div class="aquaload-footer">


    <div class="footer-logo">


        <img
            src="AQUALOAD_LOGO"
            alt="AquaLoad Logo"
        >


    </div>


    <div class="footer-center">


        <strong>

            AquaLoad

        </strong>


        <span>

            Malaysian Seafood Ordering &
            Smart Loading Platform

        </span>


    </div>


    <div class="footer-right">


        <strong>

            Smarter Loads · Fresher Seafood

        </strong>


        <span>

            Space Optimization System

        </span>


    </div>


</div>



<div class="footer-bottom">

    © 2026 AquaLoad · Final Year Project

</div>


</div>
"""


# ============================================================
# INSERT LOGO
# ============================================================

html = html.replace(
    "AQUALOAD_LOGO",
    logo_data,
)

# The original landing-page template contains its own static copies. The
# imported shared shell below is now the one header/footer used everywhere.
html = html.replace(
    "</style>",
    """.aquaload-page > .navbar,
    .aquaload-page > .aquaload-footer,
    .aquaload-page > .footer-bottom { display:none !important; }
    </style>""",
    1,
)



# ============================================================
# DISPLAY DIRECTLY ON STREAMLIT PAGE
#
# NO:
# components.html()
# iframe
# fixed height
# scrolling=True / False
#
# Only the normal website/browser scrollbar is used.
# ============================================================

render_homepage_header()

st.html(
    html,
    width="stretch",
)

render_homepage_footer(standalone=False)

