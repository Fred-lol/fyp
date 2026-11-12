import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.cards import empty_state, metric_card
from components.navigation import require_staff, staff_sidebar
from components.theme import apply_theme, page_header
from constants import ROLES, USER_STATUSES
from services.user_service import delete_user_account, load_user_management, set_user_status


bootstrap_app()
st.set_page_config(page_title="User Accounts | AquaLoad", page_icon="👥", layout="wide")
apply_theme()
staff_sidebar()
require_staff()
if "account_action" in st.query_params or "account_id" in st.query_params:
    st.query_params.clear()

# Modal state survives page navigation in Streamlit sessions. Clear stale state
# from the earlier action flow once, so entering this page never reopens an old
# account dialog.
if st.session_state.get("manage_users_modal_state_version") != 2:
    st.session_state.pop("manage_users_editing_id", None)
    st.session_state.pop("manage_users_deleting_id", None)
    st.session_state["manage_users_modal_state_version"] = 2


def _set_editing_user(user_id):
    st.session_state.manage_users_editing_id = user_id
    st.session_state.pop("manage_users_deleting_id", None)


def _set_deleting_user(user_id):
    st.session_state.manage_users_deleting_id = user_id
    st.session_state.pop("manage_users_editing_id", None)


def _save_account_changes(user_id):
    status = st.session_state[f"manage_status_{user_id}"]
    if user_id == st.session_state.user_id and status != "Active":
        st.session_state.manage_users_message = (
            "error", "You cannot deactivate the account for your active session."
        )
        return
    ok, message = set_user_status(user_id, status)
    st.session_state.manage_users_message = ("success" if ok else "error", message)
    if ok:
        st.session_state.pop("manage_users_editing_id", None)
        st.session_state.pop("manage_users_update_click", None)
        st.rerun(scope="app")


def _confirm_delete(user_id):
    if not st.session_state.get(f"manage_delete_confirm_{user_id}"):
        st.session_state.manage_users_message = (
            "error", "Confirm that you want to permanently delete this account."
        )
        return
    if user_id == st.session_state.user_id:
        st.session_state.manage_users_message = (
            "error", "You cannot delete the account for your active session."
        )
        return
    ok, message = delete_user_account(user_id)
    st.session_state.manage_users_message = ("success" if ok else "error", message)
    if ok:
        st.session_state.pop("manage_users_deleting_id", None)
        st.session_state.pop("manage_users_delete_click", None)
        st.rerun(scope="app")


def _handle_update_click(visible_rows):
    click = st.session_state.get("manage_users_update_click")
    if click and click.row < len(visible_rows):
        _set_editing_user(visible_rows[click.row]["user_id"])


def _handle_delete_click(visible_rows):
    click = st.session_state.get("manage_users_delete_click")
    if click and click.row < len(visible_rows):
        _set_deleting_user(visible_rows[click.row]["user_id"])


def _dismiss_update_dialog():
    st.session_state.pop("manage_users_editing_id", None)


def _dismiss_delete_dialog():
    st.session_state.pop("manage_users_deleting_id", None)


@st.dialog("Update account status", on_dismiss=_dismiss_update_dialog)
def _show_update_dialog(selected):
    user_id = selected["user_id"]
    st.caption(f"{selected['full_name']} · {selected['email']}")
    st.text_input("Full name", value=selected["full_name"], disabled=True)
    st.text_input("Phone number", value=selected["phone_number"] or "", disabled=True)
    st.text_input("Role", value=selected["role"], disabled=True)
    st.selectbox(
        "Account status",
        USER_STATUSES,
        index=USER_STATUSES.index(selected["status"]),
        key=f"manage_status_{user_id}",
    )
    st.caption("Only account status can be changed here. Other account details are protected.")
    st.button(
        "Update status",
        type="primary",
        on_click=_save_account_changes,
        args=(user_id,),
        use_container_width=True,
    )


@st.dialog("Delete account", on_dismiss=_dismiss_delete_dialog)
def _show_delete_dialog(selected):
    user_id = selected["user_id"]
    st.warning(
        f"Delete {selected['full_name']} ({selected['email']}) permanently? This cannot be undone."
    )
    st.checkbox(
        "I understand this action permanently deletes the account.",
        key=f"manage_delete_confirm_{user_id}",
    )
    st.button(
        "Permanently delete account",
        type="primary",
        on_click=_confirm_delete,
        args=(user_id,),
        use_container_width=True,
    )


page_header(
    "User Account Management",
    "Search customer and staff accounts, then use the row actions to manage access.",
    "Staff Administration",
)

if message := st.session_state.pop("manage_users_message", None):
    getattr(st, message[0])(message[1])

metrics_slot = st.empty()
st.write("")
search_column, role_column, status_column, sort_column = st.columns([2, 1, 1, 1])
with search_column:
    search = st.text_input("Search", placeholder="Name or email")
with role_column:
    role = st.selectbox("Role", ["All", *ROLES.values()])
with status_column:
    status = st.selectbox("Status", ["All", *USER_STATUSES])
with sort_column:
    sort = st.selectbox(
        "Sort",
        [
            "Newest first",
            "Oldest first",
            "Name (A–Z)",
            "Name (Z–A)",
            "Role (A–Z)",
        ],
    )

counts, rows = load_user_management(search, role, status, sort)
with metrics_slot.container():
    metric_columns = st.columns(3)
    with metric_columns[0]:
        metric_card("Active Customers", counts["active_customers"])
    with metric_columns[1]:
        metric_card("Active Staff", counts["active_staff"])
    with metric_columns[2]:
        metric_card("Inactive Accounts", counts["inactive"])
if not rows:
    empty_state("No user accounts match the current filters.")
    st.stop()

users_by_id = {row["user_id"]: row for row in rows}
table_rows = []
for user in rows:
    table_rows.append({
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone_number": user["phone_number"],
        "role": user["role"],
        "status": user["status"],
        "created_at": user["created_at"],
        "update": ":material/edit:",
        "delete": ":material/delete:",
    })

st.dataframe(
    pd.DataFrame(table_rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "update": st.column_config.ButtonColumn(
            "Update",
            width="small",
            help="Update this account's status",
            type="tertiary",
            on_click=_handle_update_click,
            args=(rows,),
            key="manage_users_update_click",
        ),
        "delete": st.column_config.ButtonColumn(
            "Delete",
            width="small",
            help="Delete this account",
            type="tertiary",
            on_click=_handle_delete_click,
            args=(rows,),
            key="manage_users_delete_click",
        ),
    },
    column_order=[
        "user_id", "full_name", "email", "phone_number", "role", "status", "created_at", "update", "delete"
    ],
    key="manage_users_table",
)

editing_id = st.session_state.get("manage_users_editing_id")
if editing_id in users_by_id:
    _show_update_dialog(users_by_id[editing_id])

deleting_id = st.session_state.get("manage_users_deleting_id")
if deleting_id in users_by_id:
    _show_delete_dialog(users_by_id[deleting_id])
