"""One-time, high-contrast feedback that survives a Streamlit rerun or page change."""

import streamlit as st


def flash(level: str, message: str) -> None:
    """Queue a user-visible result for the next page render."""
    if level not in {"success", "error", "warning", "info"}:
        level = "info"
    st.session_state["aq_feedback"] = (level, message)


def render_flash() -> None:
    """Render the queued result once, then remove it."""
    message = st.session_state.pop("aq_feedback", None)
    if message:
        getattr(st, message[0])(message[1])
