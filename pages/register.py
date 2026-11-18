import base64
import sys
from pathlib import Path

import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent if CURRENT_DIR.name.lower() == "pages" else CURRENT_DIR
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.alert_theme import apply_alert_theme
from components.password_feedback import render_password_feedback
from services.auth_service import (
    email_exists, is_staff_style_email, register_customer, valid_email, valid_phone,
    validate_password_strength,
)
from services.location_service import cities_for_state, malaysia_locations, postcodes_for_city
from constants import MALAYSIA_STATES

bootstrap_app()

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Create Account | AquaLoad",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_alert_theme()


# ============================================================
# PROJECT PATH
# ============================================================

LOGO_PATH = PROJECT_DIR / "AquaLoad.png"


# ============================================================
# LOAD LOGO
# ============================================================

if not LOGO_PATH.exists():

    st.error(
        "AquaLoad.png cannot be found."
    )

    st.stop()


with open(LOGO_PATH, "rb") as image_file:

    logo_base64 = base64.b64encode(
        image_file.read()
    ).decode("utf-8")


LOGO_DATA = (
    f"data:image/png;base64,{logo_base64}"
)


# ============================================================
# REGISTRATION VALIDATION
# ============================================================

def validate_password(password):
    return validate_password_strength(password)


def reset_registration_city():
    """Clear the city selection when the customer chooses another state."""
    st.session_state.pop("register_city", None)


# ============================================================
# CSS
# ============================================================

st.html(
    """
<style>


/* ============================================================
   PAGE RESET
============================================================ */

html,
body {

    margin: 0 !important;
    padding: 0 !important;

    overflow-x: hidden !important;
}


.stApp {

    min-height: 100vh;

    background:

        radial-gradient(
            circle at 8% 10%,
            rgba(0, 174, 183, 0.07),
            transparent 25%
        ),

        radial-gradient(
            circle at 92% 90%,
            rgba(0, 63, 114, 0.06),
            transparent 25%
        ),

        linear-gradient(
            180deg,
            #edf6f8 0%,
            #f8fbfc 100%
        );
}


header[data-testid="stHeader"] {

    display: none !important;
}


[data-testid="stSidebar"] {

    display: none !important;
}


[data-testid="stMain"] {

    padding: 0 !important;
}


[data-testid="stMainBlockContainer"],
.block-container {

    width: 100% !important;

    max-width: 900px !important;

    margin: 0 auto !important;

    padding:
        28px 28px
        30px !important;
}


/* ============================================================
   HEADER
============================================================ */

.aq-register-header {

    max-width: 760px;

    margin: 0 auto;

    text-align: center;
}


.aq-logo {

    display: block;

    width: 140px;
    height: 95px;

    margin:
        0 auto
        4px;

    object-fit: contain;
}


.aq-eyebrow {

    margin-bottom: 7px;

    color: #009ba4;

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2px;

    text-transform: uppercase;
}


.aq-title {

    margin: 0;

    color: #0b3958;

    font-size: 43px;

    font-weight: 800;

    line-height: 1.15;

    letter-spacing: -1.2px;
}


.aq-description {

    max-width: 640px;

    margin:
        12px auto
        24px;

    color: #6e8491;

    font-size: 14px;

    line-height: 1.7;
}


/* ============================================================
   REGISTRATION CARD
============================================================ */

[data-testid="stVerticalBlockBorderWrapper"] {

    max-width: 720px;

    margin: 0 auto;

    border:
        1px solid
        #d6e4e9 !important;

    border-radius:
        24px !important;

    background:
        rgba(
            255,
            255,
            255,
            0.98
        ) !important;

    box-shadow:
        0 16px 42px
        rgba(
            9,
            54,
            75,
            0.075
        );
}


/* Padding inside card */

[data-testid="stVerticalBlockBorderWrapper"]
[data-testid="stVerticalBlock"] {

    padding:
        8px 10px
        10px;
}


/* ============================================================
   LABELS
============================================================ */

.stTextInput label {

    color:
        #284c63 !important;

    font-size:
        13px !important;

    font-weight:
        700 !important;
}


/* ============================================================
   INPUTS
============================================================ */

.stTextInput input {

    min-height:
        50px !important;

    padding:
        0 15px !important;

    border:
        1px solid
        #d3e1e7 !important;

    border-radius:
        11px !important;

    color:
        #173a50 !important;

    background:
        #fbfdfe !important;

    font-size:
        14px !important;
}


.stTextInput input:focus {

    border-color:
        #00a8af !important;

    box-shadow:
        0 0 0
        3px
        rgba(
            0,
            168,
            175,
            0.08
        ) !important;
}


/* ============================================================
   CREATE ACCOUNT BUTTON
============================================================ */

button[kind="primary"] {

    width:
        100% !important;

    min-height:
        58px !important;

    margin-top:
        9px;

    border:
        none !important;

    border-radius:
        13px !important;

    color:
        white !important;

    background:

        linear-gradient(
            135deg,
            #087ead,
            #0db4b9
        ) !important;

    font-size:
        17px !important;

    font-weight:
        800 !important;

    box-shadow:
        0 11px 24px
        rgba(
            0,
            135,
            155,
            0.18
        );

    transition:
        all 0.2s ease;
}


button[kind="primary"]:hover {

    color:
        white !important;

    background:

        linear-gradient(
            135deg,
            #076f9b,
            #0ba2a8
        ) !important;

    transform:
        translateY(-1px);
}


/* ============================================================
   PASSWORD HINT
============================================================ */

.aq-password-hint {

    margin:
        -6px 0
        3px;

    padding-left: 3px;

    color:
        #718791;

    font-size: 10px;

    line-height: 1.5;
}


.aq-password-good {

    margin:
        -6px 0
        3px;

    padding-left: 3px;

    color:
        #13867c;

    font-size: 10px;

    font-weight: 600;

    line-height: 1.5;
}


/* ============================================================
   LOGIN TEXT LINK
============================================================ */

.aq-login-link-container {

    margin-top: 21px;

    text-align: center;
}


.aq-login-link {

    color:
        #128d99;

    font-size:
        12px;

    font-weight:
        700;

    text-decoration:
        none;

    transition:
        0.2s ease;
}


.aq-login-link:hover {

    color:
        #08737d;

    text-decoration:
        underline;
}


/* ============================================================
   FOOTER
============================================================ */

.aq-footer {

    margin-top: 17px;

    padding-bottom: 5px;

    color:
        #899da7;

    text-align:
        center;

    font-size:
        10px;
}


/* ============================================================
   RESPONSIVE
============================================================ */

@media(max-width: 700px) {

    [data-testid="stMainBlockContainer"],
    .block-container {

        padding:
            20px 16px
            25px !important;
    }


    .aq-title {

        font-size: 34px;
    }


    .aq-description {

        font-size: 13px;
    }

}

</style>
"""
)


# ============================================================
# HEADER
# ============================================================

HEADER_HTML = f"""
<div class="aq-register-header">

    <img
        src="{LOGO_DATA}"
        class="aq-logo"
        alt="AquaLoad Logo"
    >

    <div class="aq-eyebrow">

        CUSTOMER REGISTRATION

    </div>

    <div class="aq-title">

        Create Your AquaLoad Account

    </div>

    <div class="aq-description">

        Create an account to order seafood,
        manage your orders and track the latest
        status of your purchases.

    </div>

</div>
"""


st.html(
    HEADER_HTML,
    width="stretch",
)


@st.fragment
def password_fields_fragment():
    """Update password feedback without rerunning the complete registration page."""
    password_value = st.text_input(
        "Password",
        type="password",
        placeholder="8+ characters, uppercase and special character",
        key="register_password",
        autocomplete="new-password",
    )
    render_password_feedback(password_value)
    confirmation_value = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Enter your password again",
        key="register_confirm_password",
        autocomplete="new-password",
    )
    if confirmation_value:
        if password_value == confirmation_value:
            password_valid, _ = validate_password(password_value)
            if password_valid:
                st.success("Passwords match and the password is valid.")
            else:
                st.warning("Passwords match, but the password still needs the missing requirements above.")
        else:
            st.warning("Passwords do not match.")
    return password_value, confirmation_value


@st.fragment
def registration_details_fragment():
    """Keep normal registration input updates local to this part of the page."""
    full_name_value = st.text_input("Full Name", placeholder="Enter your full name", key="register_full_name", autocomplete="name")
    email_value = st.text_input("Email Address", placeholder="Enter your email address", key="register_email", autocomplete="email")
    phone_value = st.text_input("Phone Number", placeholder="Example: 0123456789", key="register_phone", autocomplete="tel")
    address_value = st.text_input("Address (optional)", placeholder="Enter your address", key="register_address", autocomplete="street-address")
    state_value = st.selectbox(
        "State / Federal Territory", MALAYSIA_STATES,
        index=MALAYSIA_STATES.index("Perlis"), key="register_state",
        on_change=reset_registration_city,
    )
    city_options = cities_for_state(state_value)
    if not city_options:
        st.error("Malaysia city and postcode data is unavailable. Check the internet connection and try again.")
        return full_name_value, email_value, phone_value, address_value, "", state_value, ""

    city_value = st.selectbox("City", city_options, key="register_city")
    postcode_value = st.selectbox(
        "Postcode", postcodes_for_city(state_value, city_value),
        key=f"register_postcode_{state_value}_{city_value}",
        help="Only postcodes valid for the selected city are shown.",
    )
    st.caption("Select your state, city and valid postcode. AquaLoad uses this location to assign a suitable collection point when you place an order.")
    return full_name_value, email_value, phone_value, address_value, city_value, state_value, postcode_value



# ============================================================
# REGISTRATION CARD
#
# We use st.container instead of st.form so that the password
# hint can respond when the customer enters a password.
# ============================================================

with st.container(
    border=True
):

    (
        full_name, email, phone_number, address,
        city, state, postcode,
    ) = registration_details_fragment()

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    password, confirm_password = password_fields_fragment()

    # --------------------------------------------------------
    # CONFIRM PASSWORD
    # --------------------------------------------------------

    # --------------------------------------------------------
    # CREATE ACCOUNT
    # --------------------------------------------------------

    create_account = st.button(
        "Create Account",
        type="primary",
        use_container_width=True,
        key="create_customer_account",
    )


# ============================================================
# PROCESS REGISTRATION
# ============================================================

if create_account:

    # --------------------------------------------------------
    # FULL NAME
    # --------------------------------------------------------

    if not full_name.strip():

        st.error(
            "Please enter your full name."
        )


    # --------------------------------------------------------
    # EMAIL EMPTY
    # --------------------------------------------------------

    elif not email.strip():

        st.error(
            "Please enter your email address."
        )


    # --------------------------------------------------------
    # EMAIL FORMAT
    # --------------------------------------------------------

    elif not valid_email(
        email.strip()
    ):

        st.error(
            "Please enter a valid email address."
        )


    # --------------------------------------------------------
    # BLOCK STAFF-STYLE EMAIL
    # --------------------------------------------------------

    elif is_staff_style_email(
        email
    ):

        st.error(
            "AquaLoad staff accounts cannot be "
            "created through customer registration."
        )


    # --------------------------------------------------------
    # EXISTING EMAIL
    # --------------------------------------------------------

    elif email_exists(
        email.strip()
    ):

        st.error(
            "An account with this email address "
            "already exists."
        )


    # --------------------------------------------------------
    # PHONE EMPTY
    # --------------------------------------------------------

    elif not phone_number.strip():

        st.error(
            "Please enter your phone number."
        )


    # --------------------------------------------------------
    # PHONE FORMAT
    # --------------------------------------------------------

    elif not valid_phone(
        phone_number
    ):

        st.error(
            "Please enter a valid phone number."
        )


    # --------------------------------------------------------
    # PASSWORD EMPTY
    # --------------------------------------------------------

    elif not password:

        st.error(
            "Please enter a password."
        )


    # --------------------------------------------------------
    # PASSWORD VALIDATION
    # --------------------------------------------------------

    else:

        password_valid, password_error = (
            validate_password(
                password
            )
        )


        if not password_valid:

            st.error(
                password_error
            )


        # ----------------------------------------------------
        # CONFIRM PASSWORD EMPTY
        # ----------------------------------------------------

        elif not confirm_password:

            st.error(
                "Please confirm your password."
            )


        # ----------------------------------------------------
        # PASSWORDS DO NOT MATCH
        # ----------------------------------------------------

        elif password != confirm_password:

            st.error(
                "Passwords do not match."
            )


        # ----------------------------------------------------
        # CREATE ACCOUNT
        # ----------------------------------------------------

        else:

            success, message = register_customer(
                full_name.strip(),
                email.strip().lower(),
                phone_number.strip(),
                address.strip(),
                city.strip(),
                state,
                postcode.strip(),
                password,
            )

            if success:
                # Registration completes here. The Customer is immediately
                # taken back to Login instead of staying on this page.
                st.session_state.registration_success = True
                st.switch_page("pages/customer_login.py")
            else:
                st.error(message)


# ============================================================
# CLICKABLE LOGIN TEXT
#
# No st.page_link()
# No Back to Login button
#
# login.py in the pages folder has the URL /login when the app
# is started through homepage.py using Streamlit's pages/
# multipage structure. :contentReference[oaicite:0]{index=0}
# ============================================================

st.html(
    """
<div class="aq-login-link-container">

    <a
        class="aq-login-link"
        href="/customer_login"
        target="_self"
    >
        Already have an AquaLoad account?
    </a>

</div>
"""
)


# ============================================================
# CUSTOMER REGISTRATION NOTE
# ============================================================

st.info("**Customer registration only.** AquaLoad staff accounts are created and managed separately by authorized personnel.")


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
<div class="aq-footer">

    © 2026 AquaLoad ·
    Smarter Loads · Fresher Seafood

</div>
"""
)
