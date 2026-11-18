import html
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.navigation import customer_sidebar, require_login, staff_sidebar
from components.theme import apply_theme, page_header
from constants import MALAYSIA_STATES, ROLES, THEME_PREFERENCES
from services.auth_service import get_user, update_profile, update_theme_preference
from services.location_service import cities_for_state, postcodes_for_city


bootstrap_app()
st.set_page_config(page_title="My Profile | AquaLoad", page_icon="👤", layout="wide")
if not st.session_state.get("logged_in") or not st.session_state.get("user_id"):
    apply_theme()
require_login()
user = get_user(st.session_state.user_id)
if user and user.get("theme_preference") and "theme_preference" not in st.session_state:
    st.session_state.theme_preference = user["theme_preference"]
apply_theme()

if st.session_state.user_role == ROLES["CUSTOMER"]:
    customer_sidebar()
else:
    staff_sidebar()

page_header("My Profile", "Review your personal information, security and AquaLoad appearance.", "Account")

user_id = user["user_id"]
edit_key = f"profile_edit_mode_{user_id}"
result_key = f"profile_save_result_{user_id}"
theme_widget_key = f"profile_theme_choice_{user_id}"
theme_result_key = f"profile_theme_result_{user_id}"
if edit_key not in st.session_state:
    st.session_state[edit_key] = False
if theme_widget_key not in st.session_state:
    st.session_state[theme_widget_key] = user.get("theme_preference") or "System"


def _key(name: str) -> str:
    return f"profile_{name}_{user_id}"


def _set_edit_values() -> None:
    state = user.get("state") if user.get("state") in MALAYSIA_STATES else "Perlis"
    cities = cities_for_state(state)
    city = user.get("city") if user.get("city") in cities else (cities[0] if cities else "")
    postcodes = postcodes_for_city(state, city)
    postcode = user.get("postcode") if user.get("postcode") in postcodes else (postcodes[0] if postcodes else "")
    for name, value in {
        "name": user.get("full_name") or "",
        "phone": user.get("phone_number") or "",
        "address": user.get("address") or "",
        "state": state,
        "city": city,
        "postcode": postcode,
    }.items():
        st.session_state[_key(name)] = value
    st.session_state[edit_key] = True


def _reset_city_for_state() -> None:
    state = st.session_state.get(_key("state"), "")
    cities = cities_for_state(state)
    city = cities[0] if cities else ""
    st.session_state[_key("city")] = city
    postcodes = postcodes_for_city(state, city)
    st.session_state[_key("postcode")] = postcodes[0] if postcodes else ""


def _reset_postcode_for_city() -> None:
    postcodes = postcodes_for_city(
        st.session_state.get(_key("state"), ""),
        st.session_state.get(_key("city"), ""),
    )
    st.session_state[_key("postcode")] = postcodes[0] if postcodes else ""


def _save_profile_pre_render() -> None:
    state = st.session_state.get(_key("state"), "")
    city = st.session_state.get(_key("city"), "")
    postcode = st.session_state.get(_key("postcode"), "")
    if not city or postcode not in postcodes_for_city(state, city):
        st.session_state[result_key] = (False, "Select a valid Malaysian state, city and postcode before saving.")
        return
    ok, message = update_profile(
        user_id,
        st.session_state.get(_key("name"), ""),
        st.session_state.get(_key("phone"), ""),
        st.session_state.get(_key("address"), ""),
        city,
        state,
        postcode,
    )
    st.session_state[result_key] = (ok, message)
    if ok:
        st.session_state.user_name = st.session_state.get(_key("name"), "").strip()
        st.session_state[edit_key] = False


def _save_appearance_pre_render() -> None:
    choice = st.session_state.get(theme_widget_key, "System")
    ok, message = update_theme_preference(user_id, choice)
    st.session_state[theme_result_key] = (ok, message)
    if ok:
        st.session_state.theme_preference = choice


def _cancel_profile_edit() -> None:
    st.session_state[edit_key] = False


def _show_feedback(ok: bool, message: str) -> None:
    (st.success if ok else st.error)(message)


def _profile_value(label: str, value: str) -> None:
    """Render a readable view-only detail instead of a disabled form input."""
    display_value = value.strip() if isinstance(value, str) and value.strip() else "Not provided"
    st.html(
        '<div class="aq-profile-field">'
        f'<span class="aq-profile-field-label">{html.escape(label)}</span>'
        f'<span class="aq-profile-field-value">{html.escape(display_value)}</span>'
        '</div>'
    )


profile_tab, security_tab, appearance_tab = st.tabs(["Personal Information", "Security", "Appearance"])

with profile_tab:
    if not st.session_state[edit_key]:
        with st.container(border=True):
            left, right = st.columns(2)
            with left:
                _profile_value("Full name", user.get("full_name") or "")
                _profile_value("Email address", user.get("email") or "")
                _profile_value("Phone number", user.get("phone_number") or "")
                _profile_value("Role", user.get("role") or "")
            with right:
                _profile_value("Address (optional)", user.get("address") or "")
                _profile_value("City", user.get("city") or "")
                _profile_value("State / Federal Territory", user.get("state") or "")
                _profile_value("Postcode", user.get("postcode") or "")
            st.button("Edit profile", type="primary", use_container_width=True, on_click=_set_edit_values)
    else:
        with st.container(border=True):
            st.caption("Update the fields below, then save. Email address and role cannot be changed here.")
            left, right = st.columns(2)
            with left:
                st.text_input("Full Name", key=_key("name"), autocomplete="name")
                st.text_input("Email Address", value=user.get("email") or "", disabled=True)
                st.text_input("Phone Number", key=_key("phone"), autocomplete="tel")
                st.text_input("Role", value=user.get("role") or "", disabled=True)
            with right:
                st.text_input("Address (Optional)", key=_key("address"), autocomplete="street-address")
                state = st.selectbox("State / Federal Territory", MALAYSIA_STATES, key=_key("state"), on_change=_reset_city_for_state)
                cities = cities_for_state(state)
                if not cities:
                    st.error("Malaysia city and postcode data is unavailable. Check the internet connection and try again.")
                else:
                    city = st.selectbox("City", cities, key=_key("city"), on_change=_reset_postcode_for_city)
                    postcodes = postcodes_for_city(state, city)
                    if not postcodes:
                        st.error("No valid postcode is available for the selected city.")
                    else:
                        st.selectbox("Postcode", postcodes, key=_key("postcode"), help="Only postcodes valid for the selected city are shown.")
            first, second = st.columns(2)
            with first:
                st.button("Save changes", type="primary", use_container_width=True, on_click=_save_profile_pre_render)
            with second:
                st.button("Cancel", type="primary", use_container_width=True, on_click=_cancel_profile_edit)
    if result := st.session_state.pop(result_key, None):
        ok, message = result
        _show_feedback(ok, message)

with security_tab:
    with st.container(border=True):
        st.markdown("### Password security")
        st.caption("Password changes use AquaLoad's verified email one-time passcode process.")
        st.write("Request a code using your registered email address, verify it, then create a strong new password.")
        if st.button("Reset password by email OTP", type="primary", use_container_width=True, key=f"profile_forgot_password_{user_id}"):
            st.switch_page("pages/forgot_password.py")

with appearance_tab:
    with st.form("appearance_form", border=True):
        st.markdown("### Appearance")
        st.radio("Theme", THEME_PREFERENCES, horizontal=True, key=theme_widget_key)
        st.form_submit_button("Save Appearance", type="primary", use_container_width=True, on_click=_save_appearance_pre_render)
    if result := st.session_state.pop(theme_result_key, None):
        ok, message = result
        _show_feedback(ok, message)
