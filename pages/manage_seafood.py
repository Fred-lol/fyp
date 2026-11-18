import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import staff_sidebar, require_staff
from components.seafood_images import seafood_image_source
from components.display import friendly_datetime
from constants import PRODUCT_STATUSES, SEAFOOD_CATEGORIES
from services.product_service import (
    list_seafood,
    seafood_summary,
    add_product,
    update_product,
    set_stock,
    delete_product,
    LEGACY_CATEGORY_ALIASES,
)

bootstrap_app()
st.set_page_config(page_title="Seafood Management | AquaLoad", page_icon="🐟", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
# Submit callbacks run before the widgets are recreated. Clear successful form
# state at the beginning of this rerun so Streamlit cannot replay old inputs.
if st.session_state.pop("seafood_clear_add_form", False):
    for key in ("new_seafood_name", "new_seafood_description", "new_seafood_image"):
        st.session_state.pop(key, None)
    st.session_state["new_seafood_category"] = SEAFOOD_CATEGORIES[0]
    st.session_state["new_seafood_status"] = PRODUCT_STATUSES[0]
    st.session_state["new_seafood_price"] = 0.0
    st.session_state["new_seafood_stock"] = 0.0
if st.session_state.get("seafood_manage_modal_state_version") != 1:
    st.session_state.pop("seafood_editing_id", None)
    st.session_state.pop("seafood_deleting_id", None)
    st.session_state["seafood_manage_modal_state_version"] = 1
page_header(
    "Seafood Management",
    "Maintain the seafood catalogue and real stock available for Customer ordering.",
    "Seafood Inventory",
)

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def database_image(uploaded):
    if not uploaded:
        return None, None
    image_bytes = uploaded.getvalue()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("Image must be 5 MB or smaller.")
    return image_bytes, uploaded.type or "image/png"


def _show_feedback(message_key):
    if message := st.session_state.pop(message_key, None):
        getattr(st, message[0])(message[1])


def _field_feedback(errors, field, helper):
    if message := errors.get(field):
        st.error(message, icon="⚠️")
    else:
        st.caption(helper)


def _validate_new_seafood():
    name = st.session_state.get("new_seafood_name", "").strip()
    description = st.session_state.get("new_seafood_description", "").strip()
    price = st.session_state.get("new_seafood_price", 0.0)
    stock = st.session_state.get("new_seafood_stock", 0.0)
    status = st.session_state.get("new_seafood_status", "Available")
    errors = {}
    if not name:
        errors["name"] = "Enter the seafood name."
    elif len(name) < 2:
        errors["name"] = "Seafood name must contain at least 2 characters."
    elif len(name) > 80:
        errors["name"] = "Seafood name cannot be longer than 80 characters."
    if price <= 0:
        errors["price"] = "Enter a price greater than RM 0.00 per kg."
    elif price > 100_000:
        errors["price"] = "Price cannot be more than RM 100,000.00 per kg."
    if stock < 0:
        errors["stock"] = "Initial stock cannot be negative."
    elif stock > 1_000_000:
        errors["stock"] = "Initial stock cannot be more than 1,000,000 kg."
    elif status == "Available" and stock <= 0:
        errors["stock"] = "Enter stock greater than 0 kg, or choose Unavailable."
    if len(description) > 500:
        errors["description"] = "Description cannot be longer than 500 characters."
    try:
        image_data, image_mime_type = database_image(st.session_state.get("new_seafood_image"))
    except ValueError as exc:
        errors["image"] = str(exc)
        image_data, image_mime_type = None, None
    return errors, image_data, image_mime_type


def _add_new_seafood():
    errors, image_data, image_mime_type = _validate_new_seafood()
    st.session_state.seafood_add_errors = errors
    st.session_state.seafood_active_tab = "Add New Seafood"
    if errors:
        return
    ok, message = add_product(
        st.session_state["new_seafood_name"].strip(),
        st.session_state["new_seafood_category"],
        st.session_state.get("new_seafood_description", "").strip(),
        "kg",
        st.session_state["new_seafood_stock"],
        st.session_state["new_seafood_status"],
        updated_by=st.session_state.user_id,
        unit_price=st.session_state["new_seafood_price"],
        image_data=image_data,
        image_mime_type=image_mime_type,
    )
    if ok:
        st.session_state.seafood_add_errors = {}
        st.session_state.seafood_add_message = ("success", message)
        st.session_state.seafood_clear_add_form = True
    elif "name" in message.lower() or "product" in message.lower():
        st.session_state.seafood_add_errors = {"name": message}
    else:
        st.session_state.seafood_add_errors = {"form": message}


def _open_edit(product_id):
    st.session_state.seafood_editing_id = product_id
    st.session_state.pop("seafood_deleting_id", None)


def _open_delete(product_id):
    st.session_state.seafood_deleting_id = product_id
    st.session_state.pop("seafood_editing_id", None)


def _edit_button_clicked(visible_products):
    click = st.session_state.get("seafood_edit_click")
    if click and click.row < len(visible_products):
        _open_edit(visible_products[click.row]["product_id"])


def _delete_button_clicked(visible_products):
    click = st.session_state.get("seafood_delete_click")
    if click and click.row < len(visible_products):
        _open_delete(visible_products[click.row]["product_id"])


def _validate_seafood_update(product_id):
    name = st.session_state.get(f"edit_seafood_name_{product_id}", "").strip()
    price = st.session_state.get(f"edit_seafood_price_{product_id}", 0.0)
    stock = st.session_state.get(f"edit_seafood_stock_{product_id}", 0.0)
    status = st.session_state.get(f"edit_seafood_status_{product_id}", "Available")
    description = st.session_state.get(f"edit_seafood_description_{product_id}", "").strip()
    errors = {}
    if not name:
        errors["name"] = "Enter the seafood name."
    elif len(name) < 2:
        errors["name"] = "Seafood name must contain at least 2 characters."
    elif len(name) > 80:
        errors["name"] = "Seafood name cannot be longer than 80 characters."
    if price <= 0:
        errors["price"] = "Enter a price greater than RM 0.00 per kg."
    elif price > 100_000:
        errors["price"] = "Price cannot be more than RM 100,000.00 per kg."
    if stock < 0:
        errors["stock"] = "Stock cannot be negative."
    elif stock > 1_000_000:
        errors["stock"] = "Stock cannot be more than 1,000,000 kg."
    elif status == "Available" and stock <= 0:
        errors["stock"] = "Enter stock greater than 0 kg, or choose Unavailable."
    if len(description) > 500:
        errors["description"] = "Description cannot be longer than 500 characters."
    try:
        image_data, image_mime_type = database_image(st.session_state.get(f"edit_seafood_image_{product_id}"))
    except ValueError as exc:
        errors["image"] = str(exc)
        image_data, image_mime_type = None, None
    return errors, image_data, image_mime_type


def _save_seafood_update(product):
    product_id = product["product_id"]
    errors, image_data, image_mime_type = _validate_seafood_update(product_id)
    st.session_state[f"seafood_update_errors_{product_id}"] = errors
    if errors:
        return
    ok, message = update_product(
        product_id,
        st.session_state[f"edit_seafood_name_{product_id}"].strip(),
        st.session_state[f"edit_seafood_category_{product_id}"],
        st.session_state.get(f"edit_seafood_description_{product_id}", "").strip(),
        "kg",
        st.session_state[f"edit_seafood_status_{product_id}"],
        unit_price=st.session_state[f"edit_seafood_price_{product_id}"],
        image_data=image_data,
        image_mime_type=image_mime_type,
    )
    if not ok:
        st.session_state[f"seafood_update_errors_{product_id}"] = {"form": message}
        return
    new_stock = st.session_state[f"edit_seafood_stock_{product_id}"]
    if float(new_stock) != float(product["stock_quantity"] or 0):
        ok, message = set_stock(
            product_id, new_stock, st.session_state.user_id,
            st.session_state.get(f"edit_seafood_stock_note_{product_id}", ""),
        )
        if not ok:
            st.session_state[f"seafood_update_errors_{product_id}"] = {"stock": message}
            return
    st.session_state.seafood_manage_message = ("success", "Seafood product updated successfully.")
    st.session_state.seafood_active_tab = "Manage Seafood"
    st.session_state.pop("seafood_editing_id", None)
    st.session_state.pop("seafood_edit_click", None)
    st.rerun(scope="app")


def _confirm_delete(product):
    product_id = product["product_id"]
    if not st.session_state.get(f"delete_seafood_confirm_{product_id}"):
        st.session_state.seafood_dialog_message = ("error", "Confirm that you want to remove this seafood product.")
        return
    ok, message = delete_product(product_id)
    if not ok and "set to Unavailable" not in message:
        st.session_state.seafood_dialog_message = ("error", message)
        return
    st.session_state.seafood_manage_message = ("success" if ok else "warning", message)
    st.session_state.seafood_active_tab = "Manage Seafood"
    st.session_state.pop("seafood_deleting_id", None)
    st.session_state.pop("seafood_delete_click", None)
    st.rerun(scope="app")


def _dismiss_edit_dialog():
    st.session_state.pop("seafood_editing_id", None)


def _dismiss_delete_dialog():
    st.session_state.pop("seafood_deleting_id", None)


@st.dialog("Edit seafood product", on_dismiss=_dismiss_edit_dialog)
def _show_edit_dialog(product):
    product_id = product["product_id"]
    errors = st.session_state.get(f"seafood_update_errors_{product_id}", {})
    _show_feedback("seafood_dialog_message")
    st.caption("Update the product details and stock. Unit is fixed to kilograms (kg).")
    first, second = st.columns(2)
    with first:
        st.text_input("Seafood name", value=product["product_name"], max_chars=80, key=f"edit_seafood_name_{product_id}")
        _field_feedback(errors, "name", "Required. Use a clear product name, up to 80 characters.")
        category = LEGACY_CATEGORY_ALIASES.get(product["category"], product["category"])
        if category not in SEAFOOD_CATEGORIES:
            category = SEAFOOD_CATEGORIES[0]
        st.selectbox("Category", SEAFOOD_CATEGORIES, index=SEAFOOD_CATEGORIES.index(category), key=f"edit_seafood_category_{product_id}")
        st.text_input("Unit (fixed)", value="kg", disabled=True)
    with second:
        st.number_input("Price (RM per kg)", min_value=0.0, value=float(product.get("unit_price") or 0), step=0.50, format="%.2f", key=f"edit_seafood_price_{product_id}")
        _field_feedback(errors, "price", "Required. Enter a price above RM 0.00 per kg.")
        st.number_input("Current stock (kg)", min_value=0.0, value=float(product["stock_quantity"] or 0), step=1.0, key=f"edit_seafood_stock_{product_id}")
        _field_feedback(errors, "stock", "Set stock to 0 only when the product is Unavailable.")
        st.selectbox("Availability status", PRODUCT_STATUSES, index=PRODUCT_STATUSES.index(product["availability_status"]), key=f"edit_seafood_status_{product_id}")
        st.file_uploader("Replace seafood image (optional)", type=["png", "jpg", "jpeg", "webp"], key=f"edit_seafood_image_{product_id}")
        _field_feedback(errors, "image", "Optional. PNG, JPG, JPEG, or WEBP; maximum 5 MB.")
    st.text_area("Description (optional)", value=product.get("description") or "", max_chars=500, key=f"edit_seafood_description_{product_id}")
    _field_feedback(errors, "description", "Optional. Add handling, freshness, or preparation details (maximum 500 characters).")
    st.text_input("Stock update note (optional)", placeholder="Example: Physical stock count", key=f"edit_seafood_stock_note_{product_id}")
    if errors.get("form"):
        st.error(errors["form"], icon="⚠️")
    st.button("Save seafood changes", type="primary", use_container_width=True, on_click=_save_seafood_update, args=(product,))


@st.dialog("Remove seafood product", on_dismiss=_dismiss_delete_dialog)
def _show_delete_dialog(product):
    product_id = product["product_id"]
    _show_feedback("seafood_dialog_message")
    st.warning(f"Remove {product['product_name']} permanently? This cannot be undone.")
    st.caption("Products used in an order are protected and will be set to Unavailable instead.")
    st.checkbox("I understand this removes the seafood product.", key=f"delete_seafood_confirm_{product_id}")
    st.button("Remove seafood", type="primary", use_container_width=True, on_click=_confirm_delete, args=(product,))


summary = seafood_summary()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Seafood Products", summary["total"])
c2.metric("Available", summary["available"])
c3.metric("Low Stock", summary["low_stock"])
c4.metric("Out of Stock", summary["out_of_stock"])

active_tab = st.session_state.pop("seafood_active_tab", "Manage Seafood")
if active_tab not in ("Manage Seafood", "Add New Seafood"):
    active_tab = "Manage Seafood"
tab_manage, tab_add = st.tabs(
    ["Manage Seafood", "Add New Seafood"], default=active_tab, key="seafood_management_tabs"
)

with tab_manage:
    _show_feedback("seafood_manage_message")
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search = st.text_input("Search Seafood", placeholder="Search seafood name")
    with f2:
        category_filter = st.selectbox("Category", ["All"] + SEAFOOD_CATEGORIES)
    with f3:
        status_filter = st.selectbox("Availability", ["All"] + PRODUCT_STATUSES)

    products = list_seafood(search, category_filter, status_filter)
    if not products:
        st.info("No seafood matches the selected filters.")
    else:
        rows = [{
            "image": seafood_image_source(product, PROJECT_DIR),
            "seafood": product["product_name"],
            "category": product["category"],
            "price": f"RM {float(product.get('unit_price') or 0):,.2f} / kg",
            "stock": f"{float(product['stock_quantity']):g} kg",
            "availability": product["availability_status"],
            "updated": friendly_datetime(product["updated_at"]),
            "edit": ":material/edit:",
            "delete": ":material/delete:",
        } for product in products]
        st.dataframe(
            pd.DataFrame(rows), use_container_width=True, hide_index=True, key="seafood_products_table",
            column_config={
                "image": st.column_config.ImageColumn("Image", width="small"),
                "edit": st.column_config.ButtonColumn(
                    "Edit", width="small", type="tertiary", help="Edit this seafood product",
                    on_click=_edit_button_clicked, args=(products,), key="seafood_edit_click",
                ),
                "delete": st.column_config.ButtonColumn(
                    "Delete", width="small", type="tertiary", help="Remove this seafood product",
                    on_click=_delete_button_clicked, args=(products,), key="seafood_delete_click",
                ),
            },
            column_order=["image", "seafood", "category", "price", "stock", "availability", "updated", "edit", "delete"],
        )
        products_by_id = {product["product_id"]: product for product in products}
        if (editing_id := st.session_state.get("seafood_editing_id")) in products_by_id:
            _show_edit_dialog(products_by_id[editing_id])
        if (deleting_id := st.session_state.get("seafood_deleting_id")) in products_by_id:
            _show_delete_dialog(products_by_id[deleting_id])

with tab_add:
    _show_feedback("seafood_add_message")
    errors = st.session_state.get("seafood_add_errors", {})
    st.subheader("Add New Seafood", anchor=False)
    submitted = False
    with st.container(border=True):
        # clear_on_submit clears the browser-held values too (including the
        # file uploader), while the session-state reset above is a safeguard.
        with st.form("add_seafood_form", clear_on_submit=True):
            a, b = st.columns(2, gap="large")
            with a:
                st.markdown("#### Product details")
                st.text_input("Seafood name", placeholder="Example: Ikan Kembung", max_chars=80, key="new_seafood_name")
                _field_feedback(errors, "name", "Required. Use a clear product name, up to 80 characters.")
                st.selectbox("Category", SEAFOOD_CATEGORIES, key="new_seafood_category")
                st.text_input("Unit (fixed)", value="kg", disabled=True)
            with b:
                st.markdown("#### Pricing and availability")
                st.number_input("Price (RM per kg)", min_value=0.0, value=0.0, step=0.50, format="%.2f", key="new_seafood_price")
                _field_feedback(errors, "price", "Required. Enter a price above RM 0.00 per kg.")
                st.number_input("Initial stock quantity (kg)", min_value=0.0, value=0.0, step=1.0, key="new_seafood_stock")
                _field_feedback(errors, "stock", "Required for Available seafood. Use Unavailable when stock is not ready.")
                st.selectbox("Availability status", PRODUCT_STATUSES, key="new_seafood_status")
                st.file_uploader("Seafood image (optional)", type=["png", "jpg", "jpeg", "webp"], key="new_seafood_image")
                _field_feedback(errors, "image", "Optional. PNG, JPG, JPEG, or WEBP; maximum 5 MB.")
            st.divider()
            st.text_area("Description (optional)", placeholder="Example: Fresh local mackerel, suitable for grilling or curry.", max_chars=500, key="new_seafood_description")
            _field_feedback(errors, "description", "Optional. Add handling, freshness, or preparation details (maximum 500 characters).")
            if errors.get("form"):
                st.error(errors["form"], icon="⚠️")
            submitted = st.form_submit_button("Add seafood", type="primary", use_container_width=True)

    # Run after the form has submitted. clear_on_submit resets the browser-held
    # controls, while the session reset at the top protects the next rerun.
    if submitted:
        _add_new_seafood()
