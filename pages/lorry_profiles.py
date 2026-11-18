import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.cards import empty_state, metric_card
from components.display import friendly_datetime
from components.navigation import require_staff, staff_sidebar
from components.theme import apply_theme, page_header
from constants import LORRY_STATUSES
from services.lorry_service import (
    MANUAL_LORRY_STATUSES,
    delete_lorry,
    list_lorries,
    MALAYSIA_LORRY_LIMITS,
    normalise_malaysian_plate,
    save_lorry,
    set_lorry_status,
)



bootstrap_app()
st.set_page_config(page_title="Lorry Profiles | AquaLoad", page_icon="🚚", layout="wide")
apply_theme()
staff_sidebar()
require_staff()

# Reset successful additions before Streamlit recreates the form widgets.
if st.session_state.pop("lorry_clear_add_form", False):
    st.session_state.pop("new_lorry_plate", None)
    st.session_state["new_lorry_length"] = 0.0
    st.session_state["new_lorry_width"] = 0.0
    st.session_state["new_lorry_height"] = 0.0
    st.session_state["new_lorry_max_weight"] = 0.0
    st.session_state["new_lorry_status"] = MANUAL_LORRY_STATUSES[0]

if st.session_state.get("lorry_profiles_modal_state_version") != 1:
    st.session_state.pop("lorry_editing_id", None)
    st.session_state.pop("lorry_deleting_id", None)
    st.session_state["lorry_profiles_modal_state_version"] = 1


def _show_feedback(message_key):
    if message := st.session_state.pop(message_key, None):
        getattr(st, message[0])(message[1])


def _validate_lorry(plate, length, width, height, max_weight):
    """Return field-level validation errors for a practical lorry profile."""
    errors = {}
    normalised_plate, plate_error = normalise_malaysian_plate(plate)
    if plate_error:
        errors["plate"] = plate_error
    for field, value, label in (
        ("length", length, "Internal length"),
        ("width", width, "Internal width"),
        ("height", height, "Internal height"),
    ):
        minimum, maximum = MALAYSIA_LORRY_LIMITS[field]
        if float(value) < minimum or float(value) > maximum:
            errors[field] = f"{label} must be between {minimum:g} cm and {maximum:g} cm."
    minimum_weight, maximum_weight = MALAYSIA_LORRY_LIMITS["weight"]
    if float(max_weight) < minimum_weight or float(max_weight) > maximum_weight:
        errors["weight"] = f"Maximum load weight must be between {minimum_weight:g} kg and {maximum_weight:,.0f} kg."
    return normalised_plate or "", errors


def _field_feedback(errors, field, helper):
    if message := errors.get(field):
        st.error(message)
    else:
        st.caption(helper)


def _save_new_lorry():
    plate = st.session_state.get("new_lorry_plate", "")
    length = st.session_state.get("new_lorry_length", 0.0)
    width = st.session_state.get("new_lorry_width", 0.0)
    height = st.session_state.get("new_lorry_height", 0.0)
    max_weight = st.session_state.get("new_lorry_max_weight", 0.0)
    status = st.session_state.get("new_lorry_status", "Available")
    normalised_plate, errors = _validate_lorry(plate, length, width, height, max_weight)
    st.session_state.lorry_add_errors = errors
    st.session_state.lorry_profiles_active_tab = "Add Lorry"
    if errors:
        return
    ok, message = save_lorry(normalised_plate, length, width, height, max_weight, status)
    if ok:
        st.session_state.lorry_add_errors = {}
        st.session_state.lorry_add_message = ("success", message)
        st.session_state.lorry_clear_add_form = True
    else:
        st.session_state.lorry_add_errors = {"plate": message}


def _open_edit(lorry_id):
    st.session_state.lorry_editing_id = lorry_id
    st.session_state.pop("lorry_deleting_id", None)


def _open_delete(lorry_id):
    st.session_state.lorry_deleting_id = lorry_id
    st.session_state.pop("lorry_editing_id", None)


def _edit_button_clicked(visible_lorries):
    click = st.session_state.get("lorry_update_click")
    if click and click.row < len(visible_lorries):
        _open_edit(visible_lorries[click.row]["lorry_id"])


def _delete_button_clicked(visible_lorries):
    click = st.session_state.get("lorry_delete_click")
    if click and click.row < len(visible_lorries):
        _open_delete(visible_lorries[click.row]["lorry_id"])


def _save_lorry_update(lorry):
    lorry_id = lorry["lorry_id"]
    status = st.session_state.get(f"edit_lorry_status_{lorry_id}", "Available")
    if status == lorry["status"]:
        st.session_state.lorry_dialog_message = ("info", "No status change was made.")
        return
    ok, message = set_lorry_status(lorry_id, status)
    if not ok:
        st.session_state.lorry_dialog_message = ("error", message)
        return
    st.session_state.lorry_manage_message = ("success", message)
    st.session_state.lorry_profiles_active_tab = "Manage Lorry Profiles"
    st.session_state.pop("lorry_editing_id", None)
    st.session_state.pop("lorry_update_click", None)
    st.rerun(scope="app")


def _confirm_delete(lorry_id):
    if not st.session_state.get(f"delete_lorry_confirm_{lorry_id}"):
        st.session_state.lorry_dialog_message = ("error", "Confirm that you want to permanently delete this lorry profile.")
        return
    ok, message = delete_lorry(lorry_id)
    if not ok:
        st.session_state.lorry_dialog_message = ("error", message)
        return
    st.session_state.lorry_manage_message = ("success", message)
    st.session_state.lorry_profiles_active_tab = "Manage Lorry Profiles"
    st.session_state.pop("lorry_deleting_id", None)
    st.session_state.pop("lorry_delete_click", None)
    st.rerun(scope="app")


def _dismiss_edit_dialog():
    st.session_state.pop("lorry_editing_id", None)


def _dismiss_delete_dialog():
    st.session_state.pop("lorry_deleting_id", None)


@st.dialog("Update lorry profile", on_dismiss=_dismiss_edit_dialog)
def _show_update_dialog(lorry):
    lorry_id = lorry["lorry_id"]
    _show_feedback("lorry_dialog_message")
    st.caption("Only the lorry status can be changed. Registration and capacity details are protected after creation.")
    st.text_input("Plate number", value=lorry["plate_number"], disabled=True)
    dimensions = st.columns(3)
    for column, label, value in (
        (dimensions[0], "Internal length (cm)", lorry["internal_length"]),
        (dimensions[1], "Internal width (cm)", lorry["internal_width"]),
        (dimensions[2], "Internal height (cm)", lorry["internal_height"]),
    ):
        with column:
            st.number_input(label, value=float(value), step=1.0, disabled=True)
    st.number_input("Maximum load weight (kg)", value=float(lorry["max_weight"]), step=1.0, disabled=True)
    if lorry["status"] == "In Transit":
        st.selectbox("Lorry status", ["In Transit"], disabled=True, key=f"edit_lorry_status_{lorry_id}")
        st.caption("In Transit is controlled automatically after boxes are loaded. Complete the trip before changing this lorry's availability.")
    else:
        st.selectbox(
            "Lorry status", MANUAL_LORRY_STATUSES,
            index=MANUAL_LORRY_STATUSES.index(lorry["status"]),
            key=f"edit_lorry_status_{lorry_id}",
        )
        st.caption("Choose Unavailable to keep this lorry out of loading optimisation.")
        st.button("Save status", type="primary", use_container_width=True, on_click=_save_lorry_update, args=(lorry,))


@st.dialog("Delete lorry profile", on_dismiss=_dismiss_delete_dialog)
def _show_delete_dialog(lorry):
    lorry_id = lorry["lorry_id"]
    _show_feedback("lorry_dialog_message")
    st.warning(f"Delete {lorry['plate_number']} permanently? This cannot be undone.")
    st.caption("Lorries already used in a loading plan are protected. Set them to Unavailable instead.")
    st.checkbox("I understand this permanently deletes the lorry profile.", key=f"delete_lorry_confirm_{lorry_id}")
    st.button("Permanently delete lorry", type="primary", use_container_width=True, on_click=_confirm_delete, args=(lorry_id,))


page_header("Lorry Profile Management", "Maintain lorry dimensions, weight capacity and availability for loading optimization.", "Loading Resources")
lorries = list_lorries()
metrics = st.columns(3)
with metrics[0]:
    metric_card("Total Lorries", len(lorries))
with metrics[1]:
    metric_card("Available", sum(lorry["status"] == "Available" for lorry in lorries))
with metrics[2]:
    metric_card("Unavailable", sum(lorry["status"] == "Unavailable" for lorry in lorries))

active_tab = st.session_state.pop("lorry_profiles_active_tab", "Manage Lorry Profiles")
if active_tab not in ("Manage Lorry Profiles", "Add Lorry"):
    active_tab = "Manage Lorry Profiles"
manage_tab, add_tab = st.tabs(["Manage Lorry Profiles", "Add Lorry"], default=active_tab, key="lorry_profiles_tabs")

with manage_tab:
    st.subheader("Manage Lorry Profiles", anchor=False)
    _show_feedback("lorry_manage_message")
    search_col, status_col = st.columns([2, 1])
    with search_col:
        search = st.text_input("Search plate number", key="lorry_search")
    with status_col:
        status = st.selectbox("Status", ["All"] + LORRY_STATUSES, key="lorry_status_filter")
    rows = list_lorries(status, search)
    if not rows:
        empty_state("No lorry profiles match the current filters.")
    else:
        table_rows = [{
            "plate_number": row["plate_number"],
            "dimensions": f"{float(row['internal_length']):g} × {float(row['internal_width']):g} × {float(row['internal_height']):g} cm",
            "maximum_weight": f"{float(row['max_weight']):,.0f} kg",
            "status": row["status"],
            "updated": friendly_datetime(row["updated_at"]),
            "update": ":material/edit:",
            "delete": ":material/delete:",
        } for row in rows]
        st.dataframe(
            pd.DataFrame(table_rows), use_container_width=True, hide_index=True, key="lorry_profiles_table",
            column_config={
                "update": st.column_config.ButtonColumn("Update", width="small", type="tertiary", help="Update this lorry", on_click=_edit_button_clicked, args=(rows,), key="lorry_update_click"),
                "delete": st.column_config.ButtonColumn("Delete", width="small", type="tertiary", help="Delete this lorry", on_click=_delete_button_clicked, args=(rows,), key="lorry_delete_click"),
            },
            column_order=["plate_number", "dimensions", "maximum_weight", "status", "updated", "update", "delete"],
        )
        by_id = {row["lorry_id"]: row for row in rows}
        if (editing_id := st.session_state.get("lorry_editing_id")) in by_id:
            _show_update_dialog(by_id[editing_id])
        if (deleting_id := st.session_state.get("lorry_deleting_id")) in by_id:
            _show_delete_dialog(by_id[deleting_id])

with add_tab:
    st.subheader("Add Lorry", anchor=False)
    _show_feedback("lorry_add_message")
    errors = st.session_state.get("lorry_add_errors", {})
    st.caption("Enter the usable internal dimensions. You can update this profile later from Manage Lorry Profiles.")
    with st.form("add_lorry_form", border=True, clear_on_submit=True):
        st.text_input("Plate number", placeholder="Example: VAB 1234", max_chars=15, key="new_lorry_plate")
        _field_feedback(errors, "plate", "Standard: VAB 1234. Official special: MALAYSIA 1 or M_M 1. Diplomatic: 14-07-UN.")
        dimensions = st.columns(3)
        for column, field, label, default in (
            (dimensions[0], "length", "Internal length (cm)", 0.0),
            (dimensions[1], "width", "Internal width (cm)", 0.0),
            (dimensions[2], "height", "Internal height (cm)", 0.0),
        ):
            with column:
                minimum, maximum = MALAYSIA_LORRY_LIMITS[field]
                st.number_input(label, min_value=0.0, max_value=maximum, value=default, step=1.0, key=f"new_lorry_{field}")
                _field_feedback(errors, field, f"{minimum:g} to {maximum:g} cm.")
        minimum_weight, maximum_weight = MALAYSIA_LORRY_LIMITS["weight"]
        st.number_input("Maximum load weight (kg)", min_value=0.0, max_value=maximum_weight, value=0.0, step=1.0, key="new_lorry_max_weight")
        _field_feedback(errors, "weight", f"{minimum_weight:g} to {maximum_weight:,.0f} kg.")
        st.selectbox("Lorry status", MANUAL_LORRY_STATUSES, key="new_lorry_status")
        st.caption("Choose Unavailable if the lorry should not be used in loading optimisation yet. In Transit is assigned automatically after boxes are loaded.")
        st.form_submit_button("Add lorry", type="primary", use_container_width=True, on_click=_save_new_lorry)
