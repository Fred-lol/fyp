import sys
from datetime import datetime
from pathlib import Path
import streamlit as st
PROJECT_DIR=Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path: sys.path.insert(0,str(PROJECT_DIR))
from bootstrap import bootstrap_app
from components.theme import apply_theme,page_header
from components.navigation import customer_sidebar
from components.cards import empty_state
from components.feedback import flash
from services.order_service import list_customer_orders,get_order,update_customer_order,cancel_order
from constants import EDITABLE_ORDER_STATUSES,CANCELLABLE_ORDER_STATUSES
bootstrap_app()


def _friendly_timestamp(value):
    if not value:
        return "Not available"
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return str(value)

st.set_page_config(page_title="My Orders | AquaLoad",page_icon="📋",layout="wide")
apply_theme(); customer_sidebar()
page_header("My Orders","View your seafood orders and manage eligible orders.","Customer Orders")
filter_ = st.radio(
    "Show",
    ["All", "Active", "Cancelled"],
    horizontal=True,
    key="my_orders_filter",
)
orders=list_customer_orders(st.session_state.user_id, filter_)
if not orders: empty_state("No orders are available in this view.")
for o in orders:
    with st.expander(f"Order #{o['order_id']} · {o['status']} · {float(o.get('total_weight_kg') or 0):g} kg · {o.get('payment_status') or 'Not Paid'}"):
        detail=get_order(o['order_id'],st.session_state.user_id)
        st.write(f"**Status:** {detail['status']}")
        st.write(f"**Collection Point:** {detail['collection_point'] or 'Not assigned yet'}")
        if detail.get("collection_assignment") == "Local Pickup":
            st.success(f"Self-pickup at {detail['collection_point']}. No lorry delivery is required.")
        st.write(f"**Total Order Weight:** {float(detail.get('total_weight_kg') or 0):g} kg")
        payment = detail.get("payment") or {}
        st.write(f"**Payment Status:** {payment.get('payment_status') or 'Not Paid'}")
        st.write(f"**Amount:** RM {float(payment.get('amount') or detail.get('total_amount') or 0):,.2f}")
        st.markdown("#### Order Progress")
        for index, history in enumerate(detail.get("history", []), start=1):
            label = "Current" if index == len(detail["history"]) else "Completed"
            st.markdown(f"**{label}: {history['status']}**")
            st.caption(f"{_friendly_timestamp(history.get('updated_at'))} · {history.get('updated_by_name') or 'System'}")
            if history.get("note"):
                st.write(history["note"])
        st.write("**Seafood Items**")
        is_paid = payment.get("payment_status") == "Paid"
        can_edit = detail["status"] in EDITABLE_ORDER_STATUSES and not is_paid
        can_cancel = detail["status"] in CANCELLABLE_ORDER_STATUSES
        quantities = {}
        for item in detail['items']:
            if can_edit:
                quantities[item['order_item_id']] = st.number_input(
                    f"{item['product_name']} ({item['unit']})",
                    min_value=0.0,
                    value=float(item['quantity']),
                    step=1.0,
                    key=f"edit_{o['order_id']}_{item['order_item_id']}",
                )
            else:
                st.write(f"- {item['product_name']}: {item['quantity']:g} {item['unit']}")
        if can_edit:
            action_columns = st.columns(4 if can_cancel else 2)
            with action_columns[0]:
                if st.button("Save Changes", key=f"save_{o['order_id']}", type="primary", use_container_width=True):
                    ok, msg = update_customer_order(o['order_id'], st.session_state.user_id, quantities)
                    if ok:
                        flash("success", msg)
                        st.rerun()
                    else:
                        st.error(msg, icon="⚠️")
            track_column = action_columns[1]
            confirm_column = action_columns[2] if can_cancel else None
            cancel_column = action_columns[3] if can_cancel else None
        else:
            action_columns = st.columns([1, 0.8, 1]) if can_cancel else st.columns(1)
            track_column = action_columns[0]
            confirm_column = action_columns[1] if can_cancel else None
            cancel_column = action_columns[2] if can_cancel else None

        with track_column:
            if st.button("Track Status", key=f"track_{o['order_id']}", use_container_width=True):
                st.session_state.selected_order_id = o['order_id']
                st.switch_page("pages/track_order.py")
        if can_cancel:
            with confirm_column:
                confirm = st.checkbox("Confirm cancellation", key=f"confirm_{o['order_id']}")
            with cancel_column:
                if st.button("Cancel Order", key=f"cancel_{o['order_id']}", type="primary", use_container_width=True, disabled=not confirm):
                    ok, msg = cancel_order(o['order_id'], st.session_state.user_id)
                    if ok:
                        flash("success", msg)
                        st.rerun()
                    else:
                        st.error(msg, icon="⚠️")
