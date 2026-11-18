import base64
import sys
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitPageNotFoundError

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.alert_theme import apply_alert_theme
from constants import STAFF_ROLES, ROLES
from services.auth_service import authenticate_user

bootstrap_app()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Login | AquaLoad",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_alert_theme()

# This route is retained only for bookmarks made before the login split.
# Send visitors to the dedicated portal pages rather than showing the old
# combined customer/staff selector.
legacy_portal = st.query_params.get("portal")
login_target = "pages/staff_login.py" if legacy_portal == "staff" else "pages/customer_login.py"
try:
    st.switch_page(login_target)
except StreamlitPageNotFoundError:
    # The page can be executed alone by Streamlit's test runner or an embed.
    # It is a legacy redirect route, so stop gracefully rather than raising.
    st.info("This legacy login link redirects to the dedicated portal in AquaLoad.")
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "portal_mode" not in st.session_state:
    st.session_state.portal_mode = "customer"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

portal_query = st.query_params.get("portal")
if portal_query in {"customer", "staff"}:
    st.session_state.portal_mode = portal_query


# ============================================================
# LOAD LOGO
# ============================================================

BASE_DIR = PROJECT_DIR
LOGO_PATH = PROJECT_DIR / "AquaLoad.png"

if not LOGO_PATH.exists():
    st.error(
        "AquaLoad.png cannot be found. "
        "Please place AquaLoad.png in the same folder as login.py."
    )
    st.stop()


with open(LOGO_PATH, "rb") as image_file:
    logo_base64 = base64.b64encode(
        image_file.read()
    ).decode("utf-8")


LOGO_DATA = f"data:image/png;base64,{logo_base64}"


# ============================================================
# AUTHENTICATION / ROLE ROUTING
# ============================================================

def complete_login(email, user):
    role = user["role"]
    st.session_state.logged_in = True
    st.session_state.user_id = user["user_id"]
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_role = role
    st.session_state.user_name = user["full_name"]
    st.session_state.theme_preference = user.get("theme_preference") or "System"

    if role == ROLES["CUSTOMER"]:
        st.switch_page("pages/customer_dashboard.py")
    else:
        st.switch_page("pages/staff_dashboard.py")


# ============================================================
# GLOBAL CSS
#
# IMPORTANT:
# Use st.html() instead of st.markdown() for HTML/CSS.
# ============================================================

st.html(
    """
<style>

/* ============================================================
   RESET STREAMLIT
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
        32px 28px
        25px !important;

}


/* ============================================================
   HEADER
============================================================ */

.aq-login-header {

    max-width: 760px;

    margin:
        0 auto;

    text-align: center;

}


.aq-login-logo {

    display: block;

    width: 145px;
    height: 100px;

    margin:
        0 auto
        6px;

    object-fit: contain;

}


.aq-eyebrow {

    margin-bottom: 8px;

    color: #009ba4;

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2px;

    text-transform: uppercase;

}


.aq-title {

    margin:
        0;

    color: #0b3958;

    font-size: 44px;

    font-weight: 800;

    line-height: 1.15;

    letter-spacing: -1.2px;

}


.aq-description {

    max-width: 650px;

    margin:
        13px auto
        25px;

    color: #6e8491;

    font-size: 14px;

    line-height: 1.7;

}


/* ============================================================
   NORMAL BUTTONS
============================================================ */

.stButton {

    width: 100%;

}


.stButton button {

    width: 100%;

    min-height: 46px;

    padding:
        7px 14px;

    border:
        1px solid #cadce4;

    border-radius: 11px;

    color: #28516a;

    background: #ffffff;

    font-size: 13px;

    font-weight: 700;

    box-shadow:
        0 3px 8px
        rgba(20, 70, 90, 0.025);

    transition:
        all 0.2s ease;

}


.stButton button:hover {

    border-color: #83cbd0;

    color: #008f97;

    background: #f4fbfb;

    transform:
        translateY(-1px);

}


/* ============================================================
   LOGIN FORM
============================================================ */

[data-testid="stForm"] {

    max-width: 720px;

    margin:
        25px auto
        0;

    padding:
        30px 34px
        33px;

    border:
        1px solid #d6e4e9 !important;

    border-radius:
        23px !important;

    background:
        rgba(
            255,
            255,
            255,
            0.98
        );

    box-shadow:
        0 16px 42px
        rgba(
            9,
            54,
            75,
            0.075
        );

}


/* ============================================================
   LABEL
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
   INPUT
============================================================ */

.stTextInput input {

    min-height:
        51px !important;

    padding:
        0 15px !important;

    border:
        1px solid #d3e1e7 !important;

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
        0 0 0 3px
        rgba(
            0,
            168,
            175,
            0.08
        ) !important;

}


/* ============================================================
   MAIN LOGIN BUTTON
============================================================ */

[data-testid="stFormSubmitButton"] {

    width: 100% !important;

}


[data-testid="stFormSubmitButton"] button {

    width:
        100% !important;

    min-height:
        58px !important;

    margin-top:
        12px;

    border:
        none !important;

    border-radius:
        13px !important;

    color:
        #ffffff !important;

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
        0.2s ease;

}


[data-testid="stFormSubmitButton"] button:hover {

    transform:
        translateY(-1px);

    color:
        white !important;

    background:

        linear-gradient(
            135deg,
            #076f9b,
            #0ba2a8
        ) !important;

}


/* ============================================================
   FOOTER
============================================================ */

.aq-footer {

    margin-top: 19px;

    padding-bottom: 5px;

    color: #899da7;

    text-align: center;

    font-size: 10px;

}


/* ============================================================
   RESPONSIVE
============================================================ */

@media(max-width: 700px) {

    [data-testid="stMainBlockContainer"],
    .block-container {

        padding:
            22px 17px
            20px !important;

    }


    .aq-title {

        font-size: 35px;

    }


    .aq-description {

        font-size: 13px;

    }


    [data-testid="stForm"] {

        padding:
            25px 21px;

    }

}

</style>
"""
)


# ============================================================
# DYNAMIC HEADER
# ============================================================

if st.session_state.portal_mode == "staff":

    eyebrow = "AQUALOAD STAFF ACCESS"

    title = "Staff Portal Login"

    description = (
        "Authorized AquaLoad staff can sign in here "
        "to access warehouse, loading and supplier operations."
    )

    submit_text = "Login to Staff Portal"


else:

    eyebrow = "AQUALOAD CUSTOMER ACCESS"

    title = "Customer Login"

    description = (
        "Sign in to browse seafood, place orders and "
        "track your customer order status."
    )

    submit_text = "Login to Customer Portal"


# ============================================================
# HEADER
#
# st.html() prevents the Base64 image and HTML tags
# from appearing as text.
# ============================================================

HEADER_HTML = f"""
<div class="aq-login-header">

    <img
        src="{LOGO_DATA}"
        class="aq-login-logo"
        alt="AquaLoad Logo"
    >

    <div class="aq-eyebrow">
        {eyebrow}
    </div>

    <div class="aq-title">
        {title}
    </div>

    <div class="aq-description">
        {description}
    </div>

</div>
"""

st.html(
    HEADER_HTML,
    width="stretch",
)

if st.session_state.pop("registration_success", False):
    st.success("Account created successfully. Please sign in.")

# ============================================================
# CUSTOMER / STAFF BUTTONS
#
# Notice the empty columns between the two buttons.
# They will no longer touch each other.
# ============================================================

(
    switch_outer_left,
    customer_column,
    switch_middle,
    staff_column,
    switch_outer_right,
) = st.columns(
    [
        0.12,
        0.32,
        0.12,
        0.32,
        0.12,
    ],
    gap="small",
)


with customer_column:

    if st.button(
        "🐟 Customer Login",
        use_container_width=True,
        key="customer_mode_button",
    ):

        st.session_state.portal_mode = "customer"
        st.query_params["portal"] = "customer"
        st.rerun()


with staff_column:

    if st.button(
        "🚚 Staff Portal",
        use_container_width=True,
        key="staff_mode_button",
    ):

        st.session_state.portal_mode = "staff"
        st.query_params["portal"] = "staff"
        st.rerun()


# ============================================================
# LOGIN FORM
# ============================================================

with st.form(
    "aquaload_login_form",
    clear_on_submit=False,
    border=True,
):

    email = st.text_input(
        "Email Address",
        placeholder="Enter your email address",
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
    )

    submitted = st.form_submit_button(
        submit_text,
        use_container_width=True,
    )


# ============================================================
# PROCESS LOGIN
# ============================================================

if submitted:

    if not email.strip():

        st.error(
            "Please enter your email address."
        )


    elif not password:

        st.error(
            "Please enter your password."
        )


    else:

        user, error = authenticate_user(
            email,
            password,
        )


        if error:

            st.error(
                error
            )


        else:

            role = user["role"]


            # =================================================
            # STAFF PORTAL MODE
            # =================================================

            if st.session_state.portal_mode == "staff":

                if role not in STAFF_ROLES:

                    st.error(
                        "This account is not authorized "
                        "to access the Staff Portal."
                    )

                else:

                    complete_login(
                        email,
                        user,
                    )


            # =================================================
            # CUSTOMER PORTAL MODE
            # =================================================

            else:

                if role != ROLES["CUSTOMER"]:

                    st.error(
                        "This is a staff account. Please use Staff Entry "
                        "from the homepage to sign in."
                    )

                else:

                    complete_login(
                        email,
                        user,
                    )


# ============================================================
# SECONDARY BUTTONS
# ============================================================

if st.session_state.portal_mode == "customer":

    (
        action_outer_left,
        forgot_column,
        action_middle,
        create_column,
        action_outer_right,
    ) = st.columns(
        [
            0.17,
            0.25,
            0.16,
            0.25,
            0.17,
        ],
        gap="small",
    )


    with forgot_column:

        if st.button(
            "Forgot Password?",
            use_container_width=True,
            key="customer_forgot_password",
        ):
            st.switch_page("pages/forgot_password.py")


    with create_column:

        if st.button(
            "Create Account",
            use_container_width=True,
            key="create_account",
        ):
            st.switch_page("pages/register.py")


    st.info("**Need staff access?** Use the Staff Entry button on the homepage. "
            "Staff accounts are managed separately from customer accounts.")


# ============================================================
# STAFF MODE
# ============================================================

else:

    (
        staff_action_left,
        staff_forgot_column,
        staff_action_right,
    ) = st.columns(
        [
            0.36,
            0.28,
            0.36,
        ]
    )


    with staff_forgot_column:

        if st.button(
            "Forgot Password?",
            use_container_width=True,
            key="staff_forgot_password",
        ):
            st.switch_page("pages/forgot_password.py")


    st.info("**Staff access only.** This portal is available to Warehouse Administrators, "
            "Loading Supervisors and Seafood Suppliers.")


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
