import html
import streamlit as st


def metric_card(label, value, help_text=""):
    safe_help = f'<div class="aq-metric-help">{html.escape(str(help_text))}</div>' if help_text else ""
    st.html(f"""
    <div class="aq-card">
      <div class="aq-metric-label">{html.escape(str(label))}</div>
      <div class="aq-metric-value">{html.escape(str(value))}</div>
      {safe_help}
    </div>
    """)


def info_card(label, value, help_text=""):
    """Compact, equal-height information card with complete wrapping values."""
    safe_help = f'<div class="aq-info-help">{html.escape(str(help_text))}</div>' if help_text else ""
    st.html(f"""
    <div class="aq-info-card">
      <div class="aq-info-label">{html.escape(str(label))}</div>
      <div class="aq-info-value">{html.escape(str(value))}</div>
      {safe_help}
    </div>
    """)


def empty_state(message):
    st.info(message)


def empty_cart(*, checkout=False):
    with st.container(border=True, key="empty_cart_state"):
        st.markdown(":material/shopping_cart: **Your cart is empty**")
        st.caption("Add seafood from the catalogue to begin your order.")
        if checkout:
            st.page_link("pages/order_seafood.py", label="Browse Seafood")
