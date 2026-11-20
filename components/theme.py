import streamlit as st
from components.alert_theme import notification_css, UI_FOUNDATION_CSS
from components.design_system import PORTAL_CSS
from components.feedback import render_flash

LIGHT_VARS = """
  --aq-navy:#063b63; --aq-dark:#031c35; --aq-blue:#087ab0; --aq-teal:#009c9a;
  --aq-cyan:#00aeb7; --aq-seafoam:#e8fbf8; --aq-bg:#ffffff; --aq-bg2:#f5fbfd;
  --aq-card:#ffffff; --aq-card2:#f9fcfd; --aq-text:#123b57; --aq-muted:#617b8d;
  --aq-border:#d7e6ec; --aq-gold:#d8a441; --aq-coral:#df7055;
  --aq-input:#ffffff; --aq-input-border:#111827; --aq-sidebar1:#052c4c; --aq-sidebar2:#063c59;
  --aq-sidebar-text:#f3fbfd; --aq-table:#ffffff; --aq-soft:#eef8fa;
  --aq-status-success-bg:#d9f5eb; --aq-status-success-text:#075f4d; --aq-status-warning-bg:#fff2cf; --aq-status-warning-text:#825700;
  --aq-status-info-bg:#dff3fb; --aq-status-info-text:#075a7e; --aq-status-danger-bg:#fde3e5; --aq-status-danger-text:#992b32;
  --aq-primary-start:#087ead; --aq-primary-end:#0db4b9; --aq-on-primary:#ffffff;
  --aq-primary-shadow:rgba(0,135,155,.18); --aq-primary-hover-start:#076f9b; --aq-primary-hover-end:#0ba2a8;
  --background-color:#ffffff!important; --secondary-background-color:#f5fbfd!important;
  --text-color:#123b57!important; --primary-color:#009c9a!important;
"""

DARK_VARS = """
  --aq-navy:#f5fbfd; --aq-dark:#041522; --aq-blue:#62c6ed; --aq-teal:#35d2ca;
  --aq-cyan:#4bdde2; --aq-seafoam:#173f42; --aq-bg:#071a27; --aq-bg2:#0a2230;
  --aq-card:#0e2938; --aq-card2:#123342; --aq-text:#f5fbfd; --aq-muted:#bfd0d9;
  --aq-border:#315363; --aq-gold:#f0c46b; --aq-coral:#ff9a80;
  --aq-input:#102f40; --aq-input-border:#b8d1da; --aq-sidebar1:#03131f; --aq-sidebar2:#082b3a;
  --aq-sidebar-text:#f7fcfd; --aq-table:#0e2938; --aq-soft:#123342;
  --aq-status-success-bg:#124e43; --aq-status-success-text:#a4f1d6; --aq-status-warning-bg:#5b4510; --aq-status-warning-text:#ffe09a;
  --aq-status-info-bg:#104a66; --aq-status-info-text:#b7e9ff; --aq-status-danger-bg:#602b33; --aq-status-danger-text:#ffb8bd;
  --aq-primary-start:#35d2ca; --aq-primary-end:#4bdde2; --aq-on-primary:#042433;
  --aq-primary-shadow:rgba(53,210,202,.22); --aq-primary-hover-start:#57e2da; --aq-primary-hover-end:#75edf0;
  --background-color:#071a27!important; --secondary-background-color:#0e2938!important;
  --text-color:#f5fbfd!important; --primary-color:#35d2ca!important;
"""

BASE_CSS = r"""
html,body{margin:0;padding:0;overflow-x:hidden}
.stApp{background:linear-gradient(180deg,var(--aq-bg) 0%,var(--aq-bg2) 100%);color:var(--aq-text)}
header[data-testid="stHeader"]{background:transparent}
/* Streamlit's sidebar expand/collapse control lives in the app header rather
   than in .stButton. Give it the same high-contrast AquaLoad treatment. */
header[data-testid="stHeader"] button[kind="header"],
header[data-testid="stHeader"] button[kind="headerNoPadding"],
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button{background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;border:0!important;border-radius:10px!important;min-width:40px!important;min-height:40px!important;opacity:1!important;box-shadow:none!important}
header[data-testid="stHeader"] button[kind="header"] *,
header[data-testid="stHeader"] button[kind="headerNoPadding"] *,
[data-testid="stSidebarCollapsedControl"] button *,
[data-testid="stSidebarCollapseButton"] button *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
header[data-testid="stHeader"] button[kind="header"]:hover,
header[data-testid="stHeader"] button[kind="headerNoPadding"]:hover,
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover{background:var(--aq-primary-hover-start)!important;color:var(--aq-on-primary)!important}
[data-testid="stMainBlockContainer"],.block-container{max-width:1280px;padding-top:1.5rem;padding-bottom:3rem}
body,p,span,label,li{color:var(--aq-text)}
h1,h2,h3,h4{color:var(--aq-navy)!important;letter-spacing:-.02em}
.aq-page-head{margin-bottom:1.4rem}.aq-eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--aq-teal);margin-bottom:.35rem}
.aq-page-title{font-size:2.25rem;font-weight:800;color:var(--aq-navy);line-height:1.1;margin:0}.aq-page-desc{margin-top:.6rem;color:var(--aq-muted);font-size:.92rem;line-height:1.65;max-width:820px}
.aq-card{background:var(--aq-card);border:1px solid var(--aq-border);border-radius:18px;padding:20px;box-shadow:0 12px 30px rgba(0,0,0,.07)}
.aq-metric-label{font-size:.72rem;color:var(--aq-muted);text-transform:uppercase;letter-spacing:.06em;font-weight:700}.aq-metric-value{font-size:1.75rem;color:var(--aq-navy);font-weight:800;margin-top:.2rem}
.aq-note{background:var(--aq-card2);border:1px solid var(--aq-border);border-radius:12px;padding:13px 16px;color:var(--aq-muted);font-size:.83rem;line-height:1.6}
.aq-profile-field{background:var(--aq-card2);border:1px solid var(--aq-border);border-radius:12px;padding:11px 14px;min-height:70px;box-sizing:border-box;margin-bottom:12px}
.aq-profile-field-label{display:block;color:var(--aq-muted)!important;font-size:.75rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px}
.aq-profile-field-value{display:block;color:var(--aq-text)!important;font-size:.98rem;font-weight:650;line-height:1.35;overflow-wrap:anywhere}

.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:11px!important;border:none!important;background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;font-size:.94rem!important;font-weight:800!important;line-height:1.2!important;letter-spacing:0!important;min-height:42px;box-shadow:none!important}
.stButton>button p,.stFormSubmitButton>button p,.stDownloadButton>button p{color:var(--aq-on-primary)!important;font-family:inherit!important;font-size:inherit!important;font-weight:inherit!important;line-height:inherit!important;letter-spacing:inherit!important;margin:0!important}
.stButton>button span:not([data-testid="stIconMaterial"]),.stFormSubmitButton>button span:not([data-testid="stIconMaterial"]),.stDownloadButton>button span:not([data-testid="stIconMaterial"]),.stButton>button svg,.stFormSubmitButton>button svg,.stDownloadButton>button svg{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover{border:none!important;color:var(--aq-on-primary)!important;background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important}
.stButton>button[kind="tertiary"]{min-height:34px!important;padding:5px 7px!important;border:none!important;background:transparent!important;box-shadow:none!important;color:var(--aq-navy)!important}
.stButton>button[kind="tertiary"]:hover{border:none!important;background:color-mix(in srgb,var(--aq-teal) 12%,transparent)!important;color:var(--aq-teal)!important}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;border:none!important;box-shadow:none!important}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover{background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;color:var(--aq-on-primary)!important}
.stButton>button[kind="primary"] p,.stButton>button[kind="primary"] span,.stFormSubmitButton>button[kind="primary"] p,.stFormSubmitButton>button[kind="primary"] span{color:var(--aq-on-primary)!important}
.stButton>button[kind="secondary"]{background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;border:none!important;box-shadow:none!important}
.stButton>button[kind="secondary"] *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important}
.stButton>button[kind="secondary"]:hover{background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;color:var(--aq-on-primary)!important}
/* Form submit buttons have an additional Streamlit wrapper.  Match normal
   action buttons exactly, including the Appearance form's Save button. */
[data-testid="stFormSubmitButton"]>button,[data-testid="stForm"] [data-testid="stFormSubmitButton"]>button{border:none!important;border-radius:11px!important;background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;font-size:.94rem!important;font-weight:800!important;line-height:1.2!important;letter-spacing:0!important;box-shadow:none!important}
[data-testid="stFormSubmitButton"]>button *,[data-testid="stForm"] [data-testid="stFormSubmitButton"]>button *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
[data-testid="stFormSubmitButton"]>button:hover,[data-testid="stForm"] [data-testid="stFormSubmitButton"]>button:hover{background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;color:var(--aq-on-primary)!important}
/* Streamlit popovers use their own trigger outside .stButton.  Keep the cart
   trigger legible in dark mode before hover, including its Material icon. */
button[data-testid="stPopoverButton"],[data-testid="stPopover"]>button,[data-testid="stPopover"]>div>button{background:var(--aq-primary-start)!important;border:none!important;border-radius:11px!important;color:var(--aq-on-primary)!important;opacity:1!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;font-size:.94rem!important;font-weight:800!important;line-height:1.2!important;letter-spacing:0!important;box-shadow:none!important}
button[data-testid="stPopoverButton"] *,[data-testid="stPopover"]>button *,[data-testid="stPopover"]>div>button *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
button[data-testid="stPopoverButton"]:hover,[data-testid="stPopover"]>button:hover,[data-testid="stPopover"]>div>button:hover{background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;color:var(--aq-on-primary)!important}
button[data-testid="stPopoverButton"]:hover *,[data-testid="stPopover"]>button:hover *,[data-testid="stPopover"]>div>button:hover *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important}

.stTextInput input,.stNumberInput input,.stTextArea textarea{border-radius:10px!important;border-color:var(--aq-input-border)!important;background:var(--aq-input)!important;color:var(--aq-text)!important;-webkit-text-fill-color:var(--aq-text)!important}
.stTextInput [data-baseweb="input"],.stNumberInput [data-baseweb="input"],.stTextArea [data-baseweb="textarea"]{border:2px solid var(--aq-input-border)!important;border-radius:10px!important;background:var(--aq-input)!important;box-shadow:none!important}
.stTextInput input:-webkit-autofill,.stTextInput input:-webkit-autofill:hover,.stTextInput input:-webkit-autofill:focus{border-color:var(--aq-input-border)!important;-webkit-text-fill-color:var(--aq-text)!important;caret-color:var(--aq-text)!important;-webkit-box-shadow:0 0 0 1000px var(--aq-input) inset!important;box-shadow:0 0 0 1000px var(--aq-input) inset!important;transition:background-color 9999s ease-out 0s!important}
.stTextInput [data-baseweb="input"] button{background:var(--aq-input)!important;border-left:1px solid var(--aq-border)!important;color:#000000!important}
.stTextInput [data-baseweb="input"] button svg,.stTextInput [data-baseweb="input"] button svg *{color:#000000!important;fill:#000000!important;stroke:#000000!important}
.stTextInput input::placeholder,.stNumberInput input::placeholder,.stTextArea textarea::placeholder{color:var(--aq-muted)!important;opacity:.85!important;-webkit-text-fill-color:var(--aq-muted)!important}
.stTextInput label,.stNumberInput label,.stTextArea label,.stSelectbox label,.stMultiSelect label,.stRadio label{color:var(--aq-text)!important}
.stTextInput label p,.stNumberInput label p,.stTextArea label p,.stSelectbox label p,.stMultiSelect label p,.stRadio label p,[data-testid="stWidgetLabel"] p{color:var(--aq-text)!important;font-size:.9rem!important;font-weight:700!important;line-height:1.35!important}
.stCaption p,[data-testid="stCaptionContainer"] p{color:var(--aq-muted)!important;font-size:.83rem!important;line-height:1.45!important;opacity:1!important}
.stMarkdown p,.stMarkdown li,[data-testid="stMain"] .stMarkdown span{color:var(--aq-text)}
.stSelectbox [data-baseweb="select"]>div,.stMultiSelect [data-baseweb="select"]>div{border-radius:10px!important;border-color:var(--aq-input-border)!important;background:var(--aq-input)!important;color:var(--aq-text)!important}
.stSelectbox [data-baseweb="select"] span,.stMultiSelect [data-baseweb="select"] span{color:var(--aq-text)!important}
/* Keep all number controls compact and intact. Streamlit renders +/- as
   separate buttons inside the input group; without explicit flex sizing the
   buttons can be clipped in narrow form columns. */
.stNumberInput{min-width:170px!important}
.stNumberInput [data-baseweb="input"]{display:flex!important;align-items:stretch!important;min-width:0!important;min-height:42px!important;overflow:hidden!important}
.stNumberInput [data-baseweb="input"] input{min-width:0!important;width:100%!important;height:42px!important;padding:0 12px!important;border:0!important;border-radius:8px 0 0 8px!important}
.stNumberInput [data-baseweb="input"] button{flex:0 0 40px!important;width:40px!important;min-width:40px!important;height:42px!important;margin:0!important;padding:0!important;border:0!important;border-left:1px solid var(--aq-border)!important;border-radius:0!important;background:var(--aq-card2)!important;color:var(--aq-text)!important;box-shadow:none!important}
.stNumberInput [data-baseweb="input"] button:last-child{border-radius:0 8px 8px 0!important}
.stNumberInput [data-baseweb="input"] button svg,.stNumberInput [data-baseweb="input"] button svg *{color:var(--aq-text)!important;fill:currentColor!important;stroke:currentColor!important}
[data-testid="stSegmentedControl"] button{background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;color:#063b63!important;opacity:1!important}
[data-testid="stSegmentedControl"] button *,[data-testid="stSegmentedControl"] button p,[data-testid="stSegmentedControl"] button span{color:#063b63!important;opacity:1!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:var(--aq-primary-start)!important;border-color:transparent!important;color:var(--aq-on-primary)!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"] *,[data-testid="stSegmentedControl"] button[aria-pressed="true"] p,[data-testid="stSegmentedControl"] button[aria-pressed="true"] span{color:var(--aq-on-primary)!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:var(--aq-card)!important;color:var(--aq-text)!important}
[role="option"],[role="option"] span{color:var(--aq-text)!important}
[role="option"]:hover{background:var(--aq-card2)!important}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus,.stSelectbox [data-baseweb="select"]>div:focus-within,.stMultiSelect [data-baseweb="select"]>div:focus-within{outline:3px solid color-mix(in srgb,var(--aq-teal) 30%,transparent)!important;outline-offset:1px!important;border-color:var(--aq-teal)!important}
.stButton>button:focus-visible,.stFormSubmitButton>button:focus-visible,.stDownloadButton>button:focus-visible{outline:3px solid var(--aq-cyan)!important;outline-offset:3px!important}
.stButton>button:disabled,.stFormSubmitButton>button:disabled,.stDownloadButton>button:disabled{background:var(--aq-soft)!important;color:var(--aq-text)!important;opacity:1!important;border-color:var(--aq-border)!important;box-shadow:none!important;cursor:not-allowed!important}
.stButton>button:disabled p,.stButton>button:disabled span,.stFormSubmitButton>button:disabled p,.stFormSubmitButton>button:disabled span,.stDownloadButton>button:disabled p,.stDownloadButton>button:disabled span{color:var(--aq-text)!important;opacity:.78!important}
.stTextInput input:disabled,.stNumberInput input:disabled,.stTextArea textarea:disabled{background:var(--aq-soft)!important;color:var(--aq-text)!important;-webkit-text-fill-color:var(--aq-text)!important;opacity:1!important}

[data-testid="stDataFrame"]{border:1px solid var(--aq-border);border-radius:14px;overflow:hidden;background:var(--aq-table)}
[data-testid="stMetric"]{background:var(--aq-card);border:1px solid var(--aq-border);border-radius:16px;padding:14px}
[data-testid="stMetricLabel"] p,[data-testid="stMetricValue"]{color:var(--aq-text)!important}
[data-testid="stForm"]{background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:16px!important;padding:8px 12px!important;box-shadow:0 10px 24px rgba(0,0,0,.05)!important}
[data-testid="stForm"] h4{margin:4px 0 12px!important;font-size:1rem!important;color:var(--aq-navy)!important}
[data-testid="stExpander"],[data-testid="stExpander"] details,[data-testid="stExpander"] summary{background:var(--aq-card)!important;border-color:var(--aq-border)!important;border-radius:14px!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *,[data-testid="stExpander"] summary p,[data-testid="stExpander"] summary span,[data-testid="stExpander"] summary svg{color:var(--aq-text)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
[data-testid="stTabs"] button p{color:var(--aq-text)!important}
[data-testid="stCaptionContainer"] p{color:var(--aq-muted)!important}
hr{border-color:var(--aq-border)!important}
/* Streamlit dialogs are portal elements; explicitly theme them for dark mode. */
[data-testid="stDialog"],
[data-testid="stDialog"] > div,
[data-testid="stDialog"][role="dialog"],
[data-testid="stDialog"] [role="dialog"],
[data-testid="stDialog"] [data-testid="stDialogContent"],
div[role="dialog"],div[role="dialog"][aria-modal="true"]{background:var(--aq-card)!important;color:var(--aq-text)!important;border:1px solid var(--aq-border)!important}
[data-testid="stDialog"] h1,[data-testid="stDialog"] h2,[data-testid="stDialog"] h3,
[data-testid="stDialog"] p,[data-testid="stDialog"] span,[data-testid="stDialog"] label,
div[role="dialog"][aria-modal="true"] h1,div[role="dialog"][aria-modal="true"] h2,div[role="dialog"][aria-modal="true"] h3,
div[role="dialog"][aria-modal="true"] p,div[role="dialog"][aria-modal="true"] span,div[role="dialog"][aria-modal="true"] label{color:var(--aq-text)!important;opacity:1!important}
[data-testid="stDialog"] button[aria-label="Close"],
[data-testid="stDialog"] button[aria-label="Close"] svg,
div[role="dialog"][aria-modal="true"] button[aria-label="Close"],
div[role="dialog"][aria-modal="true"] button[aria-label="Close"] svg{color:var(--aq-text)!important;fill:currentColor!important;stroke:currentColor!important}
[data-baseweb="modal"],[data-baseweb="modal"] > div,[data-baseweb="modal"] [role="dialog"],
.stDialog,.stDialog > div{background:var(--aq-card)!important;color:var(--aq-text)!important;border-color:var(--aq-border)!important}
/* Remove Streamlit heading permalink icons and prevent # URL fragments. */
[data-testid="stMain"] a[href^="#"],
[data-testid="stMain"] [data-testid*="Heading"] a,
[data-testid="stMain"] [data-testid*="heading"] a,
[data-testid="stMarkdownContainer"] h1 a,[data-testid="stMarkdownContainer"] h2 a,
[data-testid="stMarkdownContainer"] h3 a,[data-testid="stMarkdownContainer"] h4 a,
[data-testid="stMarkdownContainer"] h5 a,[data-testid="stMarkdownContainer"] h6 a{display:none!important;pointer-events:none!important}

[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--aq-sidebar1),var(--aq-sidebar2));border-right:none}
[data-testid="stSidebar"] *{color:var(--aq-sidebar-text)!important}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]{border-radius:10px;margin:2px 6px;padding:9px 10px}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover{background:rgba(255,255,255,.08)}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.1)!important}
[data-testid="stSidebar"] .stButton>button{background:#ffffff!important;border:1px solid #d6e6ec!important;color:#0b3d5c!important;font-weight:800!important}
[data-testid="stSidebar"] .stButton>button p,[data-testid="stSidebar"] .stButton>button span{color:#0b3d5c!important}
[data-testid="stSidebar"] .stButton>button:hover{background:#f4fbfd!important;border-color:#9fd3df!important;color:#072c42!important}
[data-testid="stSidebar"] .stButton>button:hover p,[data-testid="stSidebar"] .stButton>button:hover span{color:#072c42!important}

/* Streamlit 1.5x identifies secondary buttons with data-testid rather than
   consistently exposing kind="secondary".  Keep normal actions on the same
   theme-aware AquaLoad colour system after every later button rule. */
.stButton>button[kind="secondary"],
.stButton>button[data-testid="stBaseButton-secondary"],
.stButton [data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-secondary"]{background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;border:none!important;box-shadow:none!important}
.stButton>button[kind="secondary"] *,
.stButton>button[data-testid="stBaseButton-secondary"] *,
.stButton [data-testid="stBaseButton-secondary"] *,
button[data-testid="stBaseButton-secondary"] *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important}
.stButton>button[kind="secondary"]:hover,
.stButton>button[data-testid="stBaseButton-secondary"]:hover,
.stButton [data-testid="stBaseButton-secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover{background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;border:none!important;color:var(--aq-on-primary)!important}

/* Logout remains a neutral navigation action, rather than inheriting the
   dark Cancel treatment used in forms.  Streamlit exposes widget keys as
   st-key-* wrapper classes. */
[data-testid="stSidebar"] .st-key-customer_logout button,
[data-testid="stSidebar"] .st-key-staff_logout button{background:#ffffff!important;border:1px solid #d6e6ec!important;color:#0b3d5c!important;box-shadow:none!important}
[data-testid="stSidebar"] .st-key-customer_logout button *,
[data-testid="stSidebar"] .st-key-staff_logout button *{color:#0b3d5c!important;fill:currentColor!important;stroke:currentColor!important}

/* Data-frame toolbar controls (table, download, copy and full-screen) are
   Streamlit icon buttons rather than .stButton controls.  Give the toolbar
   its own opaque themed surface so the icons never disappear in dark mode. */
[data-testid="stElementToolbar"],
.stElementToolbar,
[data-testid="stDataFrame"] [data-testid="stElementToolbar"],
[data-testid="stDataEditor"] [data-testid="stElementToolbar"]{
  background:var(--aq-card)!important;
  border:1px solid var(--aq-border)!important;
  border-radius:10px!important;
  box-shadow:0 5px 14px rgba(0,0,0,.14)!important;
  opacity:1!important;
}
[data-testid="stElementToolbar"] button,
.stElementToolbar button,
[data-testid="stDataFrame"] [data-testid="stElementToolbar"] button,
[data-testid="stDataEditor"] [data-testid="stElementToolbar"] button{
  background:var(--aq-card2)!important;
  border:0!important;
  border-radius:7px!important;
  color:var(--aq-text)!important;
  opacity:1!important;
  box-shadow:none!important;
}
[data-testid="stElementToolbar"] button *,
.stElementToolbar button *,
[data-testid="stDataFrame"] [data-testid="stElementToolbar"] button *,
[data-testid="stDataEditor"] [data-testid="stElementToolbar"] button *{
  color:var(--aq-text)!important;
  fill:currentColor!important;
  stroke:currentColor!important;
  opacity:1!important;
}
[data-testid="stElementToolbar"] button:hover,
.stElementToolbar button:hover{
  background:color-mix(in srgb,var(--aq-teal) 18%,var(--aq-card2))!important;
  color:var(--aq-navy)!important;
}

/* Keep the toolbar as a compact row of icons.  It must not inherit the
   full-width primary-button height, background or shadow from page actions. */
[data-testid="stElementToolbar"],.stElementToolbar,div[class*="stElementToolbar"]{
  display:flex!important;
  align-items:center!important;
  gap:2px!important;
  width:max-content!important;
  padding:3px!important;
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
[data-testid="stElementToolbar"] button,.stElementToolbar button,
div[class*="stElementToolbar"] button{
  width:32px!important;
  min-width:32px!important;
  height:32px!important;
  min-height:32px!important;
  margin:0!important;
  padding:5px!important;
  background:transparent!important;
  border:0!important;
  border-radius:7px!important;
  box-shadow:none!important;
  transform:none!important;
}
[data-testid="stElementToolbar"] button:hover,.stElementToolbar button:hover,
div[class*="stElementToolbar"] button:hover{
  background:color-mix(in srgb,var(--aq-teal) 18%,transparent)!important;
  box-shadow:none!important;
  transform:none!important;
}

/* The built-in Streamlit dataframe toolbar is not an AquaLoad action and
   renders differently across Streamlit versions. Hide it globally so tables
   remain clean, stable and focused on their own row actions. */
[data-testid="stElementToolbar"],.stElementToolbar,div[class*="stElementToolbar"]{display:none!important}

/* Download buttons use a nested Streamlit wrapper. Match their text, icons,
   colour and hover behaviour to every other primary AquaLoad action. */
[data-testid="stDownloadButton"] button,.stDownloadButton button{
  background:var(--aq-primary-start)!important;
  color:var(--aq-on-primary)!important;
  border:1px solid transparent!important;
  border-radius:11px!important;
  min-height:44px!important;
  box-shadow:0 8px 18px var(--aq-primary-shadow)!important;
}
[data-testid="stDownloadButton"] button *, .stDownloadButton button *{
  color:var(--aq-on-primary)!important;
  fill:currentColor!important;
  stroke:currentColor!important;
  opacity:1!important;
}
[data-testid="stDownloadButton"] button:hover,.stDownloadButton button:hover{
  background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;
  color:var(--aq-on-primary)!important;
  box-shadow:0 11px 22px var(--aq-primary-shadow)!important;
}
/* Streamlit may render the download trigger as either a button or a link and
   applies its text colour several levels down. Cover the whole widget so it
   honours --aq-on-primary: white in Light, dark navy in Dark. */
[data-testid="stDownloadButton"], [data-testid="stDownloadButton"] *,
.stDownloadButton, .stDownloadButton *{
  color:var(--aq-on-primary)!important;
  -webkit-text-fill-color:var(--aq-on-primary)!important;
  fill:currentColor!important;
  stroke:currentColor!important;
  opacity:1!important;
}
[data-testid="stSidebar"] .st-key-customer_logout button:hover,
[data-testid="stSidebar"] .st-key-staff_logout button:hover{background:#f4fbfd!important;border-color:#9fd3df!important;color:#072c42!important}
[data-testid="stSidebar"] .st-key-customer_logout button:hover *,
[data-testid="stSidebar"] .st-key-staff_logout button:hover *{color:#072c42!important}

/* The file-upload picker is an action, not a Cancel button.  Streamlit labels
   it as a secondary button, so explicitly give it the same accessible,
   theme-aware colour treatment as other upload actions. */
[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]{background:var(--aq-primary-start)!important;border:none!important;color:var(--aq-on-primary)!important;box-shadow:0 7px 16px var(--aq-primary-shadow)!important}
[data-testid="stFileUploader"] button *,
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
[data-testid="stFileUploader"] button:hover,
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover{background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;color:var(--aq-on-primary)!important}

/*
   AquaLoad action contract
   -------------------------
   Streamlit uses several DOM shapes for primary, secondary, form-submit,
   download, popover and data-editor controls.  Keep every ordinary action
   button on one recognisable AquaLoad treatment, while leaving only compact
   icon-only controls, header controls and Logout with their intentional
   special appearances.  These rules are deliberately late in the sheet so
   they also cover controls rendered by dialogs and expanders.
*/
.stButton > button:not([kind="tertiary"]):not(:disabled),
.stFormSubmitButton > button:not(:disabled),
.stDownloadButton > button:not(:disabled),
[data-testid="stFormSubmitButton"] > button:not(:disabled),
[data-testid="stDownloadButton"] > button:not(:disabled){
  background:var(--aq-primary-start)!important;
  color:var(--aq-on-primary)!important;
  border:1px solid transparent!important;
  border-radius:11px!important;
  min-height:44px!important;
  box-shadow:0 8px 18px var(--aq-primary-shadow)!important;
  transition:transform .14s ease,box-shadow .14s ease,background .14s ease!important;
}
.stButton > button:not([kind="tertiary"]):not(:disabled):hover,
.stFormSubmitButton > button:not(:disabled):hover,
.stDownloadButton > button:not(:disabled):hover,
[data-testid="stFormSubmitButton"] > button:not(:disabled):hover,
[data-testid="stDownloadButton"] > button:not(:disabled):hover{
  background:linear-gradient(135deg,var(--aq-primary-hover-start),var(--aq-primary-hover-end))!important;
  color:var(--aq-on-primary)!important;
  transform:translateY(-1px)!important;
  box-shadow:0 11px 22px var(--aq-primary-shadow)!important;
}
.stButton > button:not([kind="tertiary"]) *,
.stFormSubmitButton > button *,
.stDownloadButton > button *,
[data-testid="stFormSubmitButton"] > button *,
[data-testid="stDownloadButton"] > button *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
/* A disabled action remains readable and clearly unavailable in both themes. */
.stButton > button:disabled,.stFormSubmitButton > button:disabled,
.stDownloadButton > button:disabled,[data-testid="stFormSubmitButton"] > button:disabled,
[data-testid="stDownloadButton"] > button:disabled{background:var(--aq-soft)!important;color:var(--aq-muted)!important;border:1px solid var(--aq-border)!important;opacity:1!important;box-shadow:none!important}
.stButton > button:disabled *,.stFormSubmitButton > button:disabled *,
.stDownloadButton > button:disabled *,[data-testid="stFormSubmitButton"] > button:disabled *,
[data-testid="stDownloadButton"] > button:disabled *{color:var(--aq-muted)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}

/* Dark-mode text contrast for dataframe DOM overlays. Canvas cells and headers
   receive native ink colors from components.tables; this rule covers the
   dataframe's own column menus without affecting unrelated popovers. */
.stDataFrameColumnMenu [role="menuitem"],
.stDataFrameColumnFormattingMenu [role="menuitem"],
.stDataFrameColumnVisibilityMenu [role="menuitem"],
.stDataFrameButtonActionMenu [role="menuitem"],
.stDataFrameStatisticsMenu,
.stDataFrameStatisticsMenu *{
  color:var(--aq-text)!important;
}
[data-testid="stDataFrame"] input,[data-testid="stDataEditor"] input{
  color:#173b58!important;
  -webkit-text-fill-color:#173b58!important;
}
[data-testid="stDataFrame"] input::placeholder,[data-testid="stDataEditor"] input::placeholder{
  color:#617b8d!important;
  -webkit-text-fill-color:#617b8d!important;
  opacity:1!important;
}

/* Tables, forms and metric cards share the same quiet surface rhythm. */
[data-testid="stDataFrame"]{box-shadow:0 7px 20px rgba(0,0,0,.05)!important}
[data-testid="stMetric"]{min-height:104px!important;display:flex!important;flex-direction:column!important;justify-content:center!important}
[data-testid="stTabs"] [data-baseweb="tab"]{font-weight:750!important;color:var(--aq-text)!important}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--aq-teal)!important}

/* Logout is navigation, not a destructive/save action: retain its familiar
   neutral appearance after the universal action-button rules above. */
[data-testid="stSidebar"] .st-key-customer_logout button,
[data-testid="stSidebar"] .st-key-staff_logout button{background:#ffffff!important;border:1px solid #d6e6ec!important;color:#0b3d5c!important;box-shadow:none!important;transform:none!important}
[data-testid="stSidebar"] .st-key-customer_logout button *,
[data-testid="stSidebar"] .st-key-staff_logout button *{color:#0b3d5c!important;fill:currentColor!important;stroke:currentColor!important}

.aq-checkout-line{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px solid var(--aq-border)}
.aq-checkout-line:last-child{border-bottom:none}.aq-money{font-weight:800;color:var(--aq-navy)}
.aq-soft-panel{background:var(--aq-soft);border:1px solid var(--aq-border);border-radius:14px;padding:16px}
@media(max-width:768px){.aq-page-title{font-size:1.75rem}.block-container{padding-left:1rem;padding-right:1rem}}
"""

# Streamlit's segmented controls inject their own light button colours.  Use
# concrete values here so the control remains readable even when a browser
# does not inherit the page CSS custom properties into its widget wrapper.
DARK_SEGMENTED_CONTROL_CSS = """
[data-testid="stSegmentedControl"] button{background:#123342!important;border:1px solid #4f7180!important;color:#f5fbfd!important;opacity:1!important}
[data-testid="stSegmentedControl"] button *,[data-testid="stSegmentedControl"] button p,[data-testid="stSegmentedControl"] button span,[data-testid="stSegmentedControl"] button svg{color:#f5fbfd!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#35d2ca!important;border-color:#35d2ca!important;color:#042433!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"] *,[data-testid="stSegmentedControl"] button[aria-pressed="true"] p,[data-testid="stSegmentedControl"] button[aria-pressed="true"] span,[data-testid="stSegmentedControl"] button[aria-pressed="true"] svg{color:#042433!important;fill:currentColor!important;stroke:currentColor!important}
"""


def _theme_css(preference: str) -> str:
    preference = (preference or "System").title()
    if preference == "Dark":
        root = f":root{{{DARK_VARS}}}"
        control_css = DARK_SEGMENTED_CONTROL_CSS
    elif preference == "Light":
        root = f":root{{{LIGHT_VARS}}}"
        control_css = ""
    else:
        root = f":root{{{LIGHT_VARS}}}@media (prefers-color-scheme: dark){{:root{{{DARK_VARS}}}}}"
        control_css = f"@media (prefers-color-scheme: dark){{{DARK_SEGMENTED_CONTROL_CSS}}}"
    return f"<style>{root}{BASE_CSS}{control_css}{UI_FOUNDATION_CSS}{PORTAL_CSS}{notification_css(preference)}</style>"


def apply_theme(preference=None):
    if preference is None:
        preference = st.session_state.get("theme_preference", "System")
    # Theme CSS must be emitted as page markup.  st.html renders in an
    # isolated component layer on some Streamlit versions, which prevents its
    # selectors from reaching native controls such as segmented buttons.
    st.markdown(_theme_css(preference), unsafe_allow_html=True)
    render_flash()


def page_header(title, description="", eyebrow="AquaLoad", back_target=None):
    """Render a consistent page heading with a predictable top-left back action."""
    if back_target is None:
        role = st.session_state.get("user_role")
        if eyebrow in {"Customer Dashboard", "Staff Dashboard"}:
            back_target = "homepage.py"
        elif role == "Customer":
            back_target = "pages/customer_dashboard.py"
        elif role:
            back_target = "pages/staff_dashboard.py"
        else:
            back_target = "homepage.py"

    if st.button(
        ":material/arrow_back:",
        key="aq_page_back",
        type="tertiary",
    ):
        st.switch_page(back_target)

    st.html(f"""
    <div class="aq-page-head">
      <div class="aq-eyebrow">{eyebrow}</div>
      <div class="aq-page-title">{title}</div>
      <div class="aq-page-desc">{description}</div>
    </div>
    """)
