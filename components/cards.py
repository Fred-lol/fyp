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


def empty_state(message):
    st.html(f'<div class="aq-empty">{html.escape(str(message))}</div>')
