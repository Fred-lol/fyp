"""The final shared AquaLoad portal design system.

It intentionally uses stable Streamlit test IDs and semantic theme tokens so
Light, Dark and System appearances keep the same layout and hierarchy.
"""

PORTAL_CSS = r"""
/* --- AquaLoad design tokens are defined by components.theme. --- */
html,body{font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}
.stApp{background:var(--aq-bg)!important;color:var(--aq-text)!important}
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stMainBlockContainer"],.block-container{max-width:1440px!important;padding:2rem 2.25rem 3rem!important}

/* Typography and page rhythm */
[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3,[data-testid="stMain"] h4{color:var(--aq-navy)!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important}
[data-testid="stMain"] h1{font-size:clamp(2rem,3vw,2.55rem)!important;line-height:1.12!important;letter-spacing:-.035em!important;margin:0!important}
[data-testid="stMain"] h2{font-size:1.55rem!important;line-height:1.25!important;letter-spacing:-.025em!important;margin:1.75rem 0 .85rem!important}
[data-testid="stMain"] h3{font-size:1.18rem!important;line-height:1.3!important;margin:1.25rem 0 .65rem!important}
[data-testid="stMain"] h4{font-size:1rem!important;line-height:1.35!important;margin:.9rem 0 .45rem!important}
[data-testid="stMain"] p,[data-testid="stMain"] li{color:var(--aq-text)!important;font-size:.94rem!important;line-height:1.55!important}
.aq-page-head{max-width:900px!important;margin:0 0 2rem!important}
.aq-eyebrow{color:var(--aq-teal)!important;font-size:.72rem!important;font-weight:800!important;letter-spacing:.14em!important;text-transform:uppercase!important}
.aq-page-title{color:var(--aq-navy)!important;font-size:clamp(2rem,3vw,2.55rem)!important;font-weight:800!important;line-height:1.12!important;letter-spacing:-.035em!important}
.aq-page-desc{color:var(--aq-muted)!important;font-size:.98rem!important;line-height:1.65!important;max-width:780px!important}

/* Shared surfaces */
.aq-card,[data-testid="stMetric"],[data-testid="stForm"],[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"]{background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:14px!important;box-shadow:0 2px 8px rgba(3,28,53,.045)!important}
.aq-card{padding:20px!important}
.aq-metric-label,[data-testid="stMetricLabel"] p{color:var(--aq-muted)!important;font-size:.72rem!important;font-weight:800!important;letter-spacing:.065em!important;text-transform:uppercase!important}
.aq-metric-value,[data-testid="stMetricValue"]{color:var(--aq-navy)!important;font-size:1.85rem!important;font-weight:800!important;line-height:1.15!important}
.aq-metric-help{color:var(--aq-muted)!important;font-size:.8rem!important;line-height:1.45!important;margin-top:6px!important}
.aq-empty{padding:28px!important;background:var(--aq-card)!important;border:1px dashed var(--aq-border)!important;border-radius:14px!important;color:var(--aq-muted)!important}
.aq-note,.aq-soft-panel{background:var(--aq-card2)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important;color:var(--aq-muted)!important}
.aq-insight{margin:14px 0!important;padding:15px 16px!important;background:var(--aq-card2)!important;border:1px solid var(--aq-border)!important;border-left:3px solid var(--aq-teal)!important;border-radius:10px!important}.aq-insight-title{margin:0 0 4px!important;color:var(--aq-navy)!important;font-size:.88rem!important;font-weight:800!important}.aq-insight p{margin:0!important;color:var(--aq-muted)!important;font-size:.9rem!important;line-height:1.55!important}

/* Forms and inputs */
[data-testid="stForm"]{padding:20px!important}
[data-testid="stWidgetLabel"] p,.stTextInput label p,.stNumberInput label p,.stTextArea label p,.stSelectbox label p,.stMultiSelect label p,.stRadio label p{color:var(--aq-text)!important;font-size:.89rem!important;font-weight:700!important;line-height:1.35!important}
[data-testid="stCaptionContainer"] p,.stCaption p{color:var(--aq-muted)!important;font-size:.8rem!important;line-height:1.45!important}
.stTextInput [data-baseweb="input"],.stNumberInput [data-baseweb="input"],.stTextArea [data-baseweb="textarea"],.stSelectbox [data-baseweb="select"]>div,.stMultiSelect [data-baseweb="select"]>div{min-height:44px!important;background:var(--aq-input)!important;border:1px solid var(--aq-input-border)!important;border-radius:10px!important;box-shadow:none!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea{color:var(--aq-text)!important;background:var(--aq-input)!important;-webkit-text-fill-color:var(--aq-text)!important;font-size:.94rem!important}
.stTextInput input::placeholder,.stNumberInput input::placeholder,.stTextArea textarea::placeholder{color:var(--aq-muted)!important;opacity:.8!important}
.stTextInput [data-baseweb="input"]:focus-within,.stNumberInput [data-baseweb="input"]:focus-within,.stTextArea [data-baseweb="textarea"]:focus-within,.stSelectbox [data-baseweb="select"]>div:focus-within,.stMultiSelect [data-baseweb="select"]>div:focus-within{border-color:var(--aq-teal)!important;box-shadow:0 0 0 3px color-mix(in srgb,var(--aq-teal) 18%,transparent)!important}
.stNumberInput{min-width:0!important}.stNumberInput [data-baseweb="input"]{overflow:hidden!important}.stNumberInput [data-baseweb="input"] button{width:38px!important;min-width:38px!important;background:var(--aq-card2)!important;border-left:1px solid var(--aq-border)!important;color:var(--aq-text)!important;box-shadow:none!important}.stNumberInput [data-baseweb="input"] button *{color:var(--aq-text)!important;fill:currentColor!important;stroke:currentColor!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;color:var(--aq-text)!important}[role="option"],[role="option"] *{color:var(--aq-text)!important}[role="option"]:hover{background:var(--aq-card2)!important}

/* Buttons: restrained, reliable and legible in every appearance. */
.stButton>button:not([kind="tertiary"]),.stFormSubmitButton>button,.stDownloadButton>button,button[data-testid="stPopoverButton"]{min-height:44px!important;border:1px solid transparent!important;border-radius:10px!important;background:var(--aq-primary-start)!important;color:var(--aq-on-primary)!important;font-size:.93rem!important;font-weight:750!important;box-shadow:0 3px 8px var(--aq-primary-shadow)!important;transition:background .16s ease,transform .16s ease,box-shadow .16s ease!important}
.stButton>button:not([kind="tertiary"]):hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover,button[data-testid="stPopoverButton"]:hover{background:var(--aq-primary-hover-start)!important;box-shadow:0 6px 14px var(--aq-primary-shadow)!important;transform:translateY(-1px)!important}
.stButton>button:not([kind="tertiary"]) *,.stFormSubmitButton>button *,.stDownloadButton>button *,button[data-testid="stPopoverButton"] *{color:var(--aq-on-primary)!important;fill:currentColor!important;stroke:currentColor!important;opacity:1!important}
.stButton>button[kind="tertiary"]{min-height:36px!important;padding:6px 8px!important;border:0!important;background:transparent!important;color:var(--aq-navy)!important;box-shadow:none!important}.stButton>button[kind="tertiary"] *{color:inherit!important;fill:currentColor!important;stroke:currentColor!important}.stButton>button[kind="tertiary"]:hover{background:var(--aq-card2)!important;color:var(--aq-teal)!important;transform:none!important}
.stButton>button:disabled,.stFormSubmitButton>button:disabled,.stDownloadButton>button:disabled{background:var(--aq-soft)!important;border-color:var(--aq-border)!important;color:var(--aq-muted)!important;box-shadow:none!important;transform:none!important}.stButton>button:disabled *,.stFormSubmitButton>button:disabled *,.stDownloadButton>button:disabled *{color:var(--aq-muted)!important}
.stButton>button:focus-visible,.stFormSubmitButton>button:focus-visible,.stDownloadButton>button:focus-visible{outline:3px solid color-mix(in srgb,var(--aq-cyan) 60%,transparent)!important;outline-offset:2px!important}

/* Data, tabs and expanding information */
[data-testid="stDataFrame"]{background:var(--aq-table)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important;overflow:hidden!important;box-shadow:none!important}
[data-testid="stVegaLiteChart"] svg{background:transparent!important}[data-testid="stVegaLiteChart"] svg text{fill:var(--aq-text)!important}[data-testid="stVegaLiteChart"] svg .mark-group path,[data-testid="stVegaLiteChart"] svg .role-axis path,[data-testid="stVegaLiteChart"] svg .role-axis line{stroke:var(--aq-border)!important}
[data-testid="stTabs"]{border-bottom:1px solid var(--aq-border)!important}[data-testid="stTabs"] [data-baseweb="tab"]{height:42px!important;padding:0 8px!important;color:var(--aq-muted)!important;font-size:.9rem!important;font-weight:750!important}[data-testid="stTabs"] [aria-selected="true"]{color:var(--aq-teal)!important;border-bottom-color:var(--aq-teal)!important}
[data-testid="stExpander"] summary{min-height:48px!important;padding:0 16px!important;color:var(--aq-text)!important;font-weight:750!important}[data-testid="stExpander"] summary *{color:var(--aq-text)!important;fill:currentColor!important;stroke:currentColor!important}
[data-testid="stSegmentedControl"] button{min-height:40px!important;background:var(--aq-card)!important;border-color:var(--aq-border)!important;color:var(--aq-text)!important}[data-testid="stSegmentedControl"] button *{color:var(--aq-text)!important}[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:var(--aq-primary-start)!important;border-color:var(--aq-primary-start)!important}[data-testid="stSegmentedControl"] button[aria-pressed="true"] *{color:var(--aq-on-primary)!important}

/* Status and catalogue helpers */
.aq-status{display:inline-flex!important;align-items:center!important;gap:6px!important;padding:4px 9px!important;border-radius:999px!important;font-size:.78rem!important;font-weight:750!important;line-height:1.25!important}.aq-status-success{background:var(--aq-status-success-bg)!important;color:var(--aq-status-success-text)!important}.aq-status-warning{background:var(--aq-status-warning-bg)!important;color:var(--aq-status-warning-text)!important}.aq-status-info{background:var(--aq-status-info-bg)!important;color:var(--aq-status-info-text)!important}.aq-status-danger{background:var(--aq-status-danger-bg)!important;color:var(--aq-status-danger-text)!important}.aq-status-neutral{background:var(--aq-card2)!important;color:var(--aq-muted)!important}
.aq-seafood-card-image{height:180px!important;background:var(--aq-card2)!important;border:1px solid var(--aq-border)!important;border-radius:10px!important;overflow:hidden!important}.aq-seafood-card-image img{width:100%!important;height:100%!important;max-height:none!important;object-fit:cover!important;object-position:center!important}

/* Sidebar is a calm navigation surface rather than a second dashboard. */
[data-testid="stSidebar"]{background:var(--aq-sidebar1)!important;border-right:1px solid color-mix(in srgb,var(--aq-sidebar-text) 13%,transparent)!important}[data-testid="stSidebar"] *{color:var(--aq-sidebar-text)!important}[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:color-mix(in srgb,var(--aq-sidebar-text) 70%,transparent)!important}[data-testid="stSidebar"] [data-testid="stPageLink"] a{min-height:42px!important;margin:2px 0!important;border-radius:9px!important;padding:0 11px!important;color:var(--aq-sidebar-text)!important}[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]{background:color-mix(in srgb,var(--aq-cyan) 19%,transparent)!important}[data-testid="stSidebar"] hr{border-color:color-mix(in srgb,var(--aq-sidebar-text) 15%,transparent)!important}
.aq-sidebar-logo{width:76px!important;margin:2px 0 14px!important;pointer-events:none!important;user-select:none!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2{margin:0 0 2px!important;color:var(--aq-sidebar-text)!important;font-size:1.25rem!important;letter-spacing:-.02em!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h5{margin:17px 0 5px!important;color:color-mix(in srgb,var(--aq-sidebar-text) 70%,transparent)!important;font-size:.68rem!important;font-weight:800!important;letter-spacing:.095em!important}

/* A concise, deliberate session state replaces an oversized alert banner. */
.st-key-session_expired_card{max-width:460px!important;margin:clamp(40px,10vh,104px) auto 0!important;padding:24px!important;background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important;box-shadow:0 10px 26px rgba(3,28,53,.10)!important}.st-key-session_expired_card [data-testid="stVerticalBlock"]{gap:18px!important}.aq-session-card{display:flex!important;align-items:flex-start!important;gap:13px!important;margin:0!important}.aq-session-icon{width:34px!important;height:34px!important;display:grid!important;place-items:center!important;flex:0 0 34px!important;border:1px solid var(--aq-border)!important;border-radius:50%!important;background:transparent!important;color:var(--aq-teal)!important;font-size:1.15rem!important;font-weight:700!important}.aq-session-title{color:var(--aq-navy)!important;font-size:1.08rem!important;font-weight:800!important;line-height:1.3!important}.aq-session-card p{margin:4px 0 0!important;color:var(--aq-muted)!important;font-size:.91rem!important;line-height:1.5!important}.st-key-session_expired_card .stButton{width:100%!important}


@media(max-width:900px){[data-testid="stMainBlockContainer"],.block-container{padding:1.4rem 1rem 2.5rem!important}.aq-page-head{margin-bottom:1.5rem!important}.aq-seafood-card-image{height:170px!important}}
"""
