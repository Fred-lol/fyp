import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.navigation import require_staff, staff_sidebar
from components.theme import apply_theme, page_header
from constants import BOX_STATUSES
from services.box_service import (
    add_inventory,
    create_box_template,
    delete_box_template,
    list_all_box_inventory,
    set_box_status,
    set_inventory,
)


bootstrap_app()
st.set_page_config(page_title="Box Management | AquaLoad", page_icon="📦", layout="wide")
apply_theme()
staff_sidebar()
require_staff()

# Form callbacks run before widgets are recreated. Reset successful forms at
# the beginning of the rerun; invalid submissions deliberately retain inputs.
if st.session_state.pop("box_clear_add_inventory_form", False):
    st.session_state["add_box_quantity"] = 1
    st.session_state.pop("add_box_note", None)
if st.session_state.pop("box_clear_template_form", False):
    st.session_state.pop("new_box_name", None)
    st.session_state["new_box_capacity"] = 0
    st.session_state["new_box_length"] = 0.0
    st.session_state["new_box_width"] = 0.0
    st.session_state["new_box_height"] = 0.0
    st.session_state["new_box_max_weight"] = 0.0
    st.session_state["new_box_opening_quantity"] = 0

if st.session_state.get("box_inventory_modal_state_version") != 1:
    st.session_state.pop("box_inventory_editing_id", None)
    st.session_state.pop("box_inventory_deleting_id", None)
    st.session_state["box_inventory_modal_state_version"] = 1


def _show_feedback(message_key):
    """Render an action message within the section that triggered it."""
    if message := st.session_state.pop(message_key, None):
        getattr(st, message[0])(message[1])


def _add_boxes(box_id):
    quantity = st.session_state.get("add_box_quantity", 0)
    note = st.session_state.get("add_box_note", "")
    ok, message = add_inventory(box_id, quantity, st.session_state.user_id, note)
    st.session_state.box_inventory_add_message = ("success" if ok else "error", message)
    st.session_state.box_inventory_active_tab = "Add Boxes"
    if ok:
        st.session_state.box_clear_add_inventory_form = True


def _create_template():
    name = st.session_state.get("new_box_name", "").strip()
    capacity = st.session_state.get("new_box_capacity", 0)
    length = st.session_state.get("new_box_length", 0.0)
    width = st.session_state.get("new_box_width", 0.0)
    height = st.session_state.get("new_box_height", 0.0)
    max_weight = st.session_state.get("new_box_max_weight", 0.0)
    opening_quantity = st.session_state.get("new_box_opening_quantity", 0)
    errors = {}
    if not name:
        errors["name"] = "Enter a clear template name, for example “120L Insulated Box”."
    if capacity <= 0:
        errors["capacity"] = "Capacity must be at least 1 litre."
    if length <= 0:
        errors["length"] = "Length must be greater than 0 cm."
    if width <= 0:
        errors["width"] = "Width must be greater than 0 cm."
    if height <= 0:
        errors["height"] = "Height must be greater than 0 cm."
    if max_weight < 0:
        errors["weight"] = "Maximum seafood weight cannot be negative."
    if opening_quantity < 0:
        errors["opening_quantity"] = "Opening quantity cannot be negative."
    if errors:
        st.session_state.box_template_errors = errors
        st.session_state.box_inventory_active_tab = "Manage Inventory"
        return

    ok, message = create_box_template(
        name, capacity, length, width, height, max_weight, opening_quantity,
    )
    st.session_state.box_template_errors = {"name": message} if not ok else {}
    st.session_state.box_inventory_manage_message = ("success" if ok else "error", message)
    st.session_state.box_inventory_active_tab = "Manage Inventory"
    if ok:
        st.session_state.box_clear_template_form = True


def _template_field_feedback(field, helper):
    message = st.session_state.get("box_template_errors", {}).get(field)
    if message:
        st.error(message)
    else:
        st.caption(helper)


def _open_edit(box_id):
    st.session_state.box_inventory_editing_id = box_id
    st.session_state.pop("box_inventory_deleting_id", None)


def _open_delete(box_id):
    st.session_state.box_inventory_deleting_id = box_id
    st.session_state.pop("box_inventory_editing_id", None)


def _edit_button_clicked(visible_boxes):
    click = st.session_state.get("box_inventory_edit_click")
    if click and click.row < len(visible_boxes):
        _open_edit(visible_boxes[click.row]["box_profile_id"])


def _delete_button_clicked(visible_boxes):
    click = st.session_state.get("box_inventory_delete_click")
    if click and click.row < len(visible_boxes):
        _open_delete(visible_boxes[click.row]["box_profile_id"])


def _save_inventory_update(box):
    box_id = box["box_profile_id"]
    quantity = st.session_state[f"edit_box_quantity_{box_id}"]
    status = st.session_state[f"edit_box_status_{box_id}"]
    note = st.session_state.get(f"edit_box_note_{box_id}", "")

    if quantity != int(box["inventory_quantity"] or 0):
        ok, message = set_inventory(box_id, quantity, st.session_state.user_id, note)
        if not ok:
            st.session_state.box_inventory_dialog_message = ("error", message)
            return
    if status != box["status"]:
        ok, message = set_box_status(box_id, status)
        if not ok:
            st.session_state.box_inventory_dialog_message = ("error", message)
            return

    st.session_state.box_inventory_manage_message = ("success", "Box inventory updated successfully.")
    st.session_state.box_inventory_active_tab = "Manage Inventory"
    st.session_state.pop("box_inventory_editing_id", None)
    st.session_state.pop("box_inventory_edit_click", None)
    st.rerun(scope="app")


def _confirm_delete(box_id):
    if not st.session_state.get(f"delete_box_confirm_{box_id}"):
        st.session_state.box_inventory_dialog_message = (
            "error", "Confirm that you want to permanently delete this box template."
        )
        return
    ok, message = delete_box_template(box_id)
    st.session_state.box_inventory_dialog_message = ("success" if ok else "error", message)
    if ok:
        st.session_state.box_inventory_manage_message = ("success", message)
        st.session_state.box_inventory_active_tab = "Manage Inventory"
        st.session_state.pop("box_inventory_dialog_message", None)
        st.session_state.pop("box_inventory_deleting_id", None)
        st.session_state.pop("box_inventory_delete_click", None)
        st.rerun(scope="app")


def _dismiss_edit_dialog():
    st.session_state.pop("box_inventory_editing_id", None)


def _dismiss_delete_dialog():
    st.session_state.pop("box_inventory_deleting_id", None)


@st.dialog("Update box inventory", on_dismiss=_dismiss_edit_dialog)
def _show_edit_dialog(box):
    box_id = box["box_profile_id"]
    _show_feedback("box_inventory_dialog_message")
    st.caption(f"{box['box_name']} · {int(box['capacity_litre'])}L")
    st.text_input(
        "Box dimensions",
        value=f"{box['length']:g} × {box['width']:g} × {box['height']:g} cm",
        disabled=True,
    )
    st.text_input(
        "Maximum seafood weight",
        value=f"{box['max_seafood_weight_kg']:g} kg",
        disabled=True,
    )
    st.caption(f"Reserved by active orders: {int(box['reserved_quantity'])}")
    st.number_input(
        "Physical quantity",
        min_value=int(box["reserved_quantity"]),
        value=int(box["inventory_quantity"] or 0),
        step=1,
        key=f"edit_box_quantity_{box_id}",
    )
    st.selectbox(
        "Template status",
        BOX_STATUSES,
        index=BOX_STATUSES.index(box["status"]),
        key=f"edit_box_status_{box_id}",
    )
    st.text_input("Update note (optional)", key=f"edit_box_note_{box_id}")
    st.button(
        "Save inventory update",
        type="primary",
        on_click=_save_inventory_update,
        args=(box,),
        use_container_width=True,
    )


@st.dialog("Delete box template", on_dismiss=_dismiss_delete_dialog)
def _show_delete_dialog(box):
    box_id = box["box_profile_id"]
    _show_feedback("box_inventory_dialog_message")
    st.warning(
        f"Delete {box['box_name']} permanently? This cannot be undone. Templates with inventory or order history are protected."
    )
    st.checkbox(
        "I understand this action permanently deletes the box template.",
        key=f"delete_box_confirm_{box_id}",
    )
    st.button(
        "Permanently delete template",
        type="primary",
        on_click=_confirm_delete,
        args=(box_id,),
        use_container_width=True,
    )


page_header(
    "Insulated Fish Storage Box Management",
    "Manage reusable box templates and physical inventory for loading operations.",
    "Loading Resources",
)

boxes = list_all_box_inventory()
if not boxes:
    st.error("No box templates are configured.")
    st.stop()

metric_columns = st.columns(3)
with metric_columns[0]:
    st.metric("Box Templates", len(boxes))
with metric_columns[1]:
    st.metric("Physical Boxes", sum(int(box["inventory_quantity"] or 0) for box in boxes))
with metric_columns[2]:
    st.metric("Currently Available", sum(int(box["available_quantity"] or 0) for box in boxes))

active_tab = st.session_state.pop("box_inventory_active_tab", "Manage Inventory")
manage_tab, add_tab = st.tabs(
    ["Manage Inventory", "Add Boxes"], default=active_tab, key="box_inventory_tabs"
)

with add_tab:
    st.subheader("Add Physical Boxes", anchor=False)
    _show_feedback("box_inventory_add_message")
    active_boxes = [box for box in boxes if box["status"] == "Active"]
    if not active_boxes:
        st.warning("There are no active box templates. Create or reactivate a template in Manage Inventory first.")
    else:
        box_map = {f"{int(box['capacity_litre'])}L · {box['box_name']}": box for box in active_boxes}
        selected_label = st.selectbox("Box template", list(box_map), key="add_box_template")
        selected = box_map[selected_label]
        a, b, c = st.columns(3)
        a.metric("Dimensions", f"{selected['length']:g} × {selected['width']:g} × {selected['height']:g} cm")
        b.metric("Maximum Weight", f"{selected['max_seafood_weight_kg']:g} kg")
        c.metric("Current Quantity", int(selected["inventory_quantity"] or 0))
        with st.form("add_box_inventory_form", clear_on_submit=True):
            st.number_input("Quantity to add", min_value=1, value=1, step=1, key="add_box_quantity")
            st.text_input("Note (optional)", placeholder="Example: New box delivery", key="add_box_note")
            st.form_submit_button(
                "Add boxes",
                type="primary",
                use_container_width=True,
                on_click=_add_boxes,
                args=(selected["box_profile_id"],),
            )

with manage_tab:
    st.subheader("Add Box Template", anchor=False)
    _show_feedback("box_inventory_manage_message")
    with st.form("create_box_template_form", border=True, clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            st.text_input("Template name", placeholder="Example: 120L Insulated Box", key="new_box_name")
            _template_field_feedback("name", "Required. Use a unique, descriptive name.")
            st.number_input("Capacity (litres)", min_value=0, value=0, step=1, key="new_box_capacity")
            _template_field_feedback("capacity", "Required. Must be 1 litre or more.")
            st.number_input("Opening quantity", min_value=0, value=0, step=1, key="new_box_opening_quantity")
            _template_field_feedback("opening_quantity", "Use 0 if no physical boxes are available yet.")
        with right:
            size_columns = st.columns(3)
            with size_columns[0]:
                st.number_input("Length (cm)", min_value=0.0, value=0.0, step=0.1, key="new_box_length")
                _template_field_feedback("length", "More than 0 cm.")
            with size_columns[1]:
                st.number_input("Width (cm)", min_value=0.0, value=0.0, step=0.1, key="new_box_width")
                _template_field_feedback("width", "More than 0 cm.")
            with size_columns[2]:
                st.number_input("Height (cm)", min_value=0.0, value=0.0, step=0.1, key="new_box_height")
                _template_field_feedback("height", "More than 0 cm.")
            st.number_input("Maximum seafood weight (kg)", min_value=0.0, value=0.0, step=0.1, key="new_box_max_weight")
            _template_field_feedback("weight", "Use 0 only when the maximum weight is not set yet.")
        st.form_submit_button("Create box template", type="primary", use_container_width=True, on_click=_create_template)

    st.subheader("Inventory History", anchor=False)
    st.caption("Update quantity or status using the edit icon. Custom templates without history can be deleted.")
    table_rows = [{
        "size": f"{int(box['capacity_litre'])}L",
        "box_name": box["box_name"],
        "dimensions": f"{box['length']:g} × {box['width']:g} × {box['height']:g} cm",
        "quantity": int(box["inventory_quantity"] or 0),
        "reserved": int(box["reserved_quantity"]),
        "available": int(box["available_quantity"]),
        "status": box["status"],
        "update": ":material/edit:",
        "delete": ":material/delete:",
    } for box in boxes]
    st.dataframe(
        pd.DataFrame(table_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "update": st.column_config.ButtonColumn(
                "Update", width="small", type="tertiary", help="Update quantity or status",
                on_click=_edit_button_clicked, args=(boxes,), key="box_inventory_edit_click",
            ),
            "delete": st.column_config.ButtonColumn(
                "Delete", width="small", type="tertiary", help="Delete this box template",
                on_click=_delete_button_clicked, args=(boxes,), key="box_inventory_delete_click",
            ),
        },
        column_order=[
            "size", "box_name", "dimensions", "quantity", "reserved", "available", "status", "update", "delete"
        ],
        key="box_inventory_table",
    )

    by_id = {box["box_profile_id"]: box for box in boxes}
    editing_id = st.session_state.get("box_inventory_editing_id")
    if editing_id in by_id:
        _show_edit_dialog(by_id[editing_id])
    deleting_id = st.session_state.get("box_inventory_deleting_id")
    if deleting_id in by_id:
        _show_delete_dialog(by_id[deleting_id])
