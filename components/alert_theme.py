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


# Each palette entry is (surface, text, border, icon).
LIGHT = {
    "info": ("#EDF7FD", "#164B69", "#B6DCEF", "#17638A"),
    "error": ("#FFF1F2", "#872D3A", "#F2BEC4", "#AC3443"),
    "success": ("#EAF8F1", "#155D43", "#ADDDC4", "#19724F"),
    "warning": ("#FFF8E8", "#76511A", "#EBD6A3", "#A06B1B"),
}
DARK = {
    "info": ("#142F40", "#D6ECF8", "#315D75", "#83CAE9"),
    "error": ("#39252D", "#FFE0E4", "#87505D", "#F2A0A9"),
    "success": ("#17392F", "#D5F7E8", "#35725D", "#7DDDB3"),
    "warning": ("#403322", "#FFEBC7", "#8A6B39", "#F2C477"),
}

# Inline masks use the icon colour from the active palette without a font download.
ICON_PATHS = {
    "info": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 11v6 M12 7v.2",
    "error": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M8.5 8.5l7 7 M15.5 8.5l-7 7",
    "success": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M7 12l3.5 3.5L17 9",
    "warning": "M11 3.5a1.2 1.2 0 0 1 2 0l9 16a1 1 0 0 1-1 1.5H3a1 1 0 0 1-1-1.5z M12 9v5 M12 17v.2",
}


def _tokens(palette):
    declarations = [
        f"--aq-{kind}-{part}:{colour};"
        for kind, colours in palette.items()
        for part, colour in zip(("surface", "ink", "line", "icon"), colours)
    ]
    return ":root{" + "".join(declarations) + "}"


def _variants():
    rules = []
    for kind, path in ICON_PATHS.items():
        panel = f'[data-testid="stAlertContainer"]:has([data-testid="stAlertContent{kind.title()}"])'
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
               f"<path d='{path}' fill='none' stroke='black' stroke-width='1.8' "
               "stroke-linecap='round' stroke-linejoin='round'/></svg>")
        rules.append(f"{panel}, .aq-notice[data-kind={kind}] {{"
                     f"--surface:var(--aq-{kind}-surface); --ink:var(--aq-{kind}-ink); "
                     f"--line:var(--aq-{kind}-line); --icon:var(--aq-{kind}-icon); "
                     f'--symbol:url("data:image/svg+xml,{svg}"); }}')
    return "\n".join(rules)


PANEL_CSS = """
/* Keep Streamlit's live-region wrapper and let each message size to its own
   content. Long messages stop at the available column width and wrap there. */
[data-testid="stAlert"]{width:100%!important;margin:.25rem 0 .65rem!important;background:transparent!important;border:0!important;box-shadow:none!important;padding:0!important;overflow:visible!important}
[data-testid="stAlertContainer"]:has([data-testid^="stAlertContent"]), .aq-notice {
    display: inline-flex;
    align-items: flex-start;
    gap: 9px;
    box-sizing: border-box;
    width: fit-content;
    max-width: min(100%, 76rem);
    min-width: 0;
    margin: 0;
    padding: 10px 13px;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--surface);
    color: var(--ink);
    box-shadow: none;
    text-align: left;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.45;
    overflow-wrap: anywhere;
    vertical-align: top;
}
[data-testid="stAlertContainer"]:has([data-testid^="stAlertContent"]):not(:has([data-testid*="Icon"]))::before, .aq-notice::before {
    content: "";
    flex: 0 0 17px;
    width: 17px;
    height: 17px;
    margin-top: 1px;
    background: var(--icon);
    mask: var(--symbol) center / contain no-repeat;
}
[data-testid="stAlertContainer"] [data-testid^="stAlertContent"] {
    flex: 1;
    min-width: 0;
    margin: 0;
    padding: 0;
    overflow-wrap: anywhere;
    word-break: normal;
}
/* Streamlit offsets its final paragraph with a negative wrapper margin. */
[data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] {
    margin: 0;
    min-width: 0;
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: normal;
}
/* Portal, dialog and public form text rules otherwise override inherited ink. */
[data-testid="stAlert"] [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"],
[data-testid="stAlert"] [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] :is(p, span, strong, em, li, code, a, pre) {
    color: var(--ink) !important;
    -webkit-text-fill-color: currentColor;
    font-size: 14px !important;
    line-height: 1.45 !important;
    text-align: left;
    white-space: normal !important;
}
[data-testid="stAlert"] [data-testid="stAlertContainer"] p {
    margin: 0;
    font-weight: 400 !important;
}
[data-testid="stAlert"] [data-testid="stAlertContainer"] p + p { margin-top: .45em; }
[data-testid="stAlert"] [data-testid="stAlertContainer"] :is(pre, code) {
    max-width: 100%;
    white-space: pre-wrap !important;
    overflow-wrap: anywhere;
}
[data-testid="stAlert"] [data-testid="stAlertContainer"] a { text-decoration: underline; }
[data-testid="stAlertContainer"] [data-testid*="Icon"] {
    color: var(--icon) !important;
    font-size: 17px;
    flex: 0 0 17px;
}
[data-testid="stException"] [data-testid="stExceptionMessage"] :is(span, strong, code) {
    color: var(--ink);
}
.st-key-empty_cart_state {
    max-width: 42rem;
    padding: 15px;
    border: 1px solid var(--aq-border);
    border-radius: 9px;
    background: var(--aq-card2);
}
.st-key-empty_cart_state [data-testid="stCaptionContainer"] p {
    color: var(--aq-muted);
    font-size: 14px !important;
    line-height: 1.5 !important;
}

@media (max-width: 640px) {
  [data-testid="stAlertContainer"]:has([data-testid^="stAlertContent"]), .aq-notice {
    max-width: 100%;
    padding: 9px 11px;
    gap: 8px;
    font-size: 13px;
  }
  [data-testid="stAlert"] [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] :is(p, span, strong, em, li, code, a, pre) {
    font-size: 13px !important;
  }
}
"""


def notification_css(preference="System"):
    preference = (preference or "System").title()
    tokens = _tokens(DARK if preference == "Dark" else LIGHT)
    if preference == "System":
        tokens += "@media (prefers-color-scheme: dark){" + _tokens(DARK) + "}"
    return tokens + _variants() + PANEL_CSS


def apply_alert_theme() -> None:
    """Use the same notification styles on public and authenticated pages."""
    css = notification_css(st.session_state.get("theme_preference", "System"))
    st.markdown(f"<style>{UI_FOUNDATION_CSS}{css}</style>", unsafe_allow_html=True)
