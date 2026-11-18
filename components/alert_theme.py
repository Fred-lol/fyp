"""Shared, accessible message styling for every AquaLoad page."""

import streamlit as st


UI_FOUNDATION_CSS = r"""
/* Shared AquaLoad visual foundation.  This final layer keeps native Streamlit
   widgets, HTML panels and page-level content aligned across the application. */
:root{font-family:Inter,"Segoe UI",Arial,sans-serif}
.stApp,[data-testid="stAppViewContainer"]{font-family:Inter,"Segoe UI",Arial,sans-serif!important}
[data-testid="stMainBlockContainer"],.block-container{max-width:1280px!important;padding-top:1.75rem!important;padding-bottom:3.25rem!important}
[data-testid="stMain"] h1{font-size:clamp(2rem,3vw,2.65rem)!important;line-height:1.12!important;letter-spacing:-.035em!important;margin:0 0 .55rem!important}
[data-testid="stMain"] h2{font-size:clamp(1.45rem,2.2vw,1.85rem)!important;line-height:1.22!important;letter-spacing:-.022em!important;margin:1.75rem 0 .85rem!important}
[data-testid="stMain"] h3{font-size:1.18rem!important;line-height:1.3!important;margin:1.25rem 0 .65rem!important}
[data-testid="stMain"] h4{font-size:1rem!important;line-height:1.35!important;margin:1rem 0 .5rem!important}
[data-testid="stMain"] p,[data-testid="stMain"] li{font-size:.95rem!important;line-height:1.6!important}
.aq-page-desc{font-size:.98rem!important;line-height:1.65!important;max-width:760px!important}
.aq-eyebrow{font-size:.72rem!important;letter-spacing:.13em!important}
[data-testid="stWidgetLabel"] p,.stTextInput label p,.stNumberInput label p,.stTextArea label p,.stSelectbox label p,.stMultiSelect label p,.stRadio label p{font-size:.9rem!important;font-weight:750!important;line-height:1.35!important}
[data-testid="stCaptionContainer"] p,.stCaption p{font-size:.82rem!important;line-height:1.5!important}

/* Reusable surfaces: quiet borders, predictable radius and comfortable space. */
[data-testid="stForm"],[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"]{border-radius:16px!important}
[data-testid="stForm"]{padding:18px 20px!important}
[data-testid="stMetric"]{border-radius:16px!important;padding:18px!important;min-height:112px!important}
[data-testid="stMetricLabel"] p{font-size:.72rem!important;font-weight:800!important;letter-spacing:.06em!important;text-transform:uppercase!important}
[data-testid="stMetricValue"]{font-size:1.8rem!important;line-height:1.12!important}
[data-testid="stDataFrame"]{border-radius:13px!important;overflow:hidden!important}
[data-testid="stTabs"] [data-baseweb="tab"]{min-height:42px!important;padding:0 4px!important;font-size:.92rem!important;font-weight:750!important}
[data-testid="stExpander"] summary{min-height:48px!important;padding:0 15px!important;font-weight:750!important}

/* Inputs share an accessible, calm size without the cramped appearance. */
.stTextInput input,.stNumberInput input,.stTextArea textarea{font-size:.95rem!important;line-height:1.45!important}
.stTextInput [data-baseweb="input"],.stNumberInput [data-baseweb="input"],.stTextArea [data-baseweb="textarea"],.stSelectbox [data-baseweb="select"]>div,.stMultiSelect [data-baseweb="select"]>div{min-height:44px!important;border-radius:10px!important}
.stTextArea textarea{min-height:105px!important}

/* Actions have one visual language in every appearance. */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{min-height:44px!important;border-radius:10px!important;font-size:.94rem!important;font-weight:800!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2{font-size:1.12rem!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h5{font-size:.72rem!important;letter-spacing:.06em!important}

@media(max-width:768px){
  [data-testid="stMainBlockContainer"],.block-container{padding:1.1rem 1rem 2.5rem!important}
  [data-testid="stMain"] h1{font-size:2rem!important}
  [data-testid="stMain"] h2{font-size:1.4rem!important}
  [data-testid="stMetric"]{min-height:96px!important;padding:14px!important}
  [data-testid="stForm"]{padding:14px!important}
}
"""


# Streamlit can render an outer stAlertContainer around an inner stAlert
# panel.  Only the inner panel is painted, so feedback never looks layered.
ALERT_CSS = r"""
/* AquaLoad feedback: success = green, confirmation/info = blue, error = red.
   Fixed, high-contrast colours keep messages visible in all appearances. */
[data-testid="stAlertContainer"],
[data-testid="stAlertContainer"][role="alert"]{
  margin:0!important;padding:0!important;background:transparent!important;
  border:0!important;border-radius:0!important;box-shadow:none!important;
}
[data-testid="stAlert"],
[data-testid="stAlertContainer"] [data-testid="stAlert"],
[data-testid="stAlertContainer"] [role="alert"]{
  margin:8px 0 14px!important;padding:0!important;
  border-radius:14px!important;border-width:1px!important;border-style:solid!important;
  overflow:hidden!important;box-shadow:0 4px 12px rgba(0,0,0,.11)!important;color:#fff!important;opacity:1!important;
}
/* Successful completed action. */
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]),
[role="alert"]:has([data-testid="stAlertContentSuccess"]),
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) [data-testid="stAlert"],
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) [role="alert"]{background:#08765f!important;border-color:#43d8ad!important}
/* Confirmation, guidance and neutral information. Warnings are confirmations,
   so they use the same blue treatment instead of a fourth alert colour. */
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]),
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),
[role="alert"]:has([data-testid="stAlertContentInfo"]),
[role="alert"]:has([data-testid="stAlertContentWarning"]),
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) [data-testid="stAlert"],
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) [data-testid="stAlert"],
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) [role="alert"],
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) [role="alert"]{background:#075f8c!important;border-color:#59cdfb!important}
/* Validation and failed actions. */
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]),
[role="alert"]:has([data-testid="stAlertContentError"]),
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) [data-testid="stAlert"],
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) [role="alert"]{background:#972a31!important;border-color:#ff979b!important}
[data-testid="stAlert"] *,
[data-testid="stAlertContainer"] [data-testid="stAlert"] *,
[data-testid="stAlertContainer"] [role="alert"] *{color:#fff!important;-webkit-text-fill-color:#fff!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
/* Streamlit has a wrapper div on some versions. Reset it first, then give
   only the actual alert-content element one compact, deliberate padding. */
[data-testid="stAlert"] > div:not([data-testid^="stAlertContent"]),
[data-testid="stAlertContainer"] [role="alert"] > div:not([data-testid^="stAlertContent"]){padding:0!important;margin:0!important}
[data-testid^="stAlertContent"]{
  display:flex!important;align-items:center!important;justify-content:center!important;gap:10px!important;
  padding:13px 18px!important;
  text-align:center!important;
}
[data-testid^="stAlertContent"] > div{min-width:0!important;text-align:center!important}
[data-testid="stAlert"] p,
[data-testid="stAlertContainer"] [data-testid="stAlert"] p,
[data-testid="stAlertContainer"] [role="alert"] p{margin:0!important;font-size:.94rem!important;font-weight:650!important;line-height:1.45!important}
"""


def apply_alert_theme() -> None:
    """Inject shared UI and alert styles for public pages without apply_theme."""
    st.markdown(f"<style>{UI_FOUNDATION_CSS}{ALERT_CSS}</style>", unsafe_allow_html=True)
