import streamlit as st

from services.auth_service import password_requirement_status


def render_password_feedback(password: str) -> None:
    """Show password requirements and a live completion bar below an input."""
    st.caption("Password requirements: 8+ characters, 1 uppercase letter, and 1 special character.")
    if not password:
        return

    status = password_requirement_status(password)
    completed = sum(status.values())
    st.progress(completed / len(status), text=f"Password requirements completed: {completed} of {len(status)}")
    rules = (
        ("At least 8 characters", status["minimum_length"]),
        ("At least 1 uppercase letter", status["uppercase_letter"]),
        ("At least 1 special character", status["special_character"]),
    )
    missing = [label.lower() for label, valid in rules if not valid]
    if missing:
        st.warning("To make your password valid, add " + " and ".join(missing) + ".")
    else:
        st.success("Password meets all requirements.")
    for label, valid in rules:
        st.caption(f"{'✓' if valid else '○'} {label}")
