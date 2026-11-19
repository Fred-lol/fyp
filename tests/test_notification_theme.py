from components.alert_theme import DARK, LIGHT, notification_css
from pathlib import Path
import ast


def test_all_message_types_have_theme_aware_semantic_tokens():
    css = notification_css("Light")
    for kind in ("success", "error", "warning", "info"):
        assert f"[data-testid=\"stAlertContainer\"]:has([data-testid=\"stAlertContent{kind.title()}\"])" in css
        assert f"--aq-{kind}-surface:{LIGHT[kind][0]}" in css
        assert f"--aq-{kind}-ink:{LIGHT[kind][1]}" in css


def test_dark_theme_notification_colours_are_emitted():
    css = notification_css("Dark")
    for kind in ("success", "error", "warning", "info"):
        assert f"--aq-{kind}-surface:{DARK[kind][0]}" in css
        assert f"--aq-{kind}-ink:{DARK[kind][1]}" in css


def test_system_theme_uses_operating_system_preference():
    css = notification_css("System")
    assert "@media (prefers-color-scheme: dark)" in css
    for kind in ("success", "error", "warning", "info"):
        assert f"--aq-{kind}-surface:{DARK[kind][0]}" in css


def test_notifications_fit_their_content_and_wrap_long_messages():
    css = notification_css("Light")
    assert "width: fit-content" in css
    assert "max-width: min(100%, 76rem)" in css
    assert "overflow-wrap: anywhere" in css
    assert "white-space: pre-wrap !important" in css
    assert "@media (max-width: 640px)" in css
    assert "width: 100%;\n    max-width: none" not in css


def test_every_page_with_native_messages_loads_the_shared_notification_theme():
    message_methods = {"success", "error", "warning", "info", "toast"}
    pages = Path(__file__).resolve().parents[1] / "pages"
    uncovered = []
    for page in pages.glob("*.py"):
        tree = ast.parse(page.read_text(encoding="utf-8"))
        has_message = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in message_methods
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            for node in ast.walk(tree)
        )
        has_shared_theme = any(
            marker in page.read_text(encoding="utf-8")
            for marker in ("apply_theme", "apply_alert_theme", "render_public_login_header", "notification_css")
        )
        if has_message and not has_shared_theme:
            uncovered.append(page.name)
    assert uncovered == []
