from pathlib import Path

from streamlit.testing.v1 import AppTest

from components.navigation import (
    _clear_expired_session_state,
    _expired_login_target,
    _session_expired_css,
)


def test_expired_redirect_resolves_portal_before_clearing_identity():
    state = {
        "logged_in": False,
        "user_id": 12,
        "user_role": "Warehouse Administrator",
        "portal_mode": "staff",
    }

    destination = _expired_login_target(None, state)
    _clear_expired_session_state(state)

    assert destination == "pages/staff_login.py"
    assert "user_id" not in state
    assert "user_role" not in state


def test_expired_redirect_honours_customer_role_and_preserves_theme():
    state = {
        "logged_in": False,
        "user_role": "Customer",
        "theme_preference": "Dark",
        "catalogue_search": "salmon",
    }

    assert _expired_login_target(None, state) == "pages/customer_login.py"
    _clear_expired_session_state(state)
    assert state["theme_preference"] == "Dark"
    assert state["catalogue_search"] == "salmon"


def test_expired_layout_hides_navigation_and_centers_fullscreen_card():
    css = _session_expired_css()
    assert '[data-testid="stSidebar"]' in css
    assert "position:fixed" in css
    assert "align-items:center" in css
    assert "justify-content:center" in css


def test_expired_customer_screen_has_no_sidebar_and_redirects_cleanly():
    root = str(Path(__file__).resolve().parents[1])
    script = f"""
import sys
sys.path.insert(0, {root!r})
import streamlit as st
from components.navigation import require_login
if not st.session_state.get('fixture_initialized'):
    st.session_state.fixture_initialized = True
    st.session_state.logged_in = False
    st.session_state.user_id = 42
    st.session_state.user_role = 'Customer'
    st.session_state.theme_preference = 'Light'
    st.session_state.cart = {{7: 15}}
st.switch_page = lambda page: st.session_state.update({{'redirected_to': page}})
require_login()
st.write('Protected content')
"""
    app = AppTest.from_string(script).run()

    assert not app.exception
    assert len(app.sidebar) == 0
    assert any("Session Expired" in str(element.value) for element in app.html)
    assert not any("Protected content" in str(element.value) for element in app.markdown)

    app.button[0].click().run()
    assert app.session_state["redirected_to"] == "pages/customer_login.py"
    assert "user_id" not in app.session_state
    assert "cart" not in app.session_state
    assert app.session_state["theme_preference"] == "Light"


def test_valid_session_continues_without_expired_screen():
    app = AppTest.from_string(
        """
import streamlit as st
from components.navigation import require_login
st.session_state.logged_in = True
st.session_state.user_id = 42
require_login()
st.write('Protected content')
"""
    ).run()

    assert not app.exception
    assert any("Protected content" in str(element.value) for element in app.markdown)
    assert not app.button
