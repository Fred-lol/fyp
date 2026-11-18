import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import customer_sidebar
from services.payment_service import (
    MALAYSIAN_BANKS,
    MALAYSIAN_EWALLETS,
    PAYMENT_METHODS,
    checkout_summary,
    complete_demo_payment,
    validate_payment_details,
)
from services.collection_point_service import list_collection_points
from services.auth_service import get_user

bootstrap_app()
st.set_page_config(page_title="Payment | AquaLoad", page_icon="💳", layout="wide")
apply_theme(); customer_sidebar()
page_header(
    "Order Review & Payment",
    "Review your seafood order and complete the checkout interface before the order is submitted.",
    "Customer Checkout",
    back_target="pages/order_seafood.py",
)


def _field_feedback(errors, field, helper):
    if message := errors.get(field):
        st.error(message, icon="⚠️")
    else:
        st.caption(helper)


def _format_card_number():
    """Format Malaysian Visa/Mastercard and American Express card numbers."""
    digits = "".join(char for char in st.session_state.get("payment_card_number", "") if char.isdigit())[:19]
    groups = (4, 6, 5) if digits.startswith(("34", "37")) else (4, 4, 4, 4)
    parts, position = [], 0
    for group_size in groups:
        part = digits[position:position + group_size]
        if not part:
            break
        parts.append(part)
        position += group_size
    formatted = "-".join(parts)
    separator_points = {sum(groups[:index]) for index in range(1, len(groups))}
    st.session_state.payment_card_number = f"{formatted}-" if len(digits) in separator_points else formatted


def _format_expiry_date():
    """Convert four entered expiry digits into the MM/YY display format."""
    digits = "".join(char for char in st.session_state.get("payment_card_expiry", "") if char.isdigit())[:4]
    st.session_state.payment_card_expiry = (
        f"{digits[:2]}/{digits[2:]}" if len(digits) >= 2 else digits
    )


def _render_card_input_masks():
    """Format card fields in the browser as the customer types, without storing details."""
    components.html(
        """
        <script>
        (() => {
          const documentRoot = window.parent.document;
          const nativeSetter = Object.getOwnPropertyDescriptor(
            window.parent.HTMLInputElement.prototype, "value"
          ).set;

          const setValue = (input, value) => {
            nativeSetter.call(input, value);
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.setSelectionRange(value.length, value.length);
          };

          const formatCard = (value) => {
            const digits = value.replace(/\\D/g, "").slice(0, 19);
            const groups = /^(34|37)/.test(digits) ? [4, 6, 5] : [4, 4, 4, 4];
            const parts = [];
            let position = 0;
            for (const group of groups) {
              const part = digits.slice(position, position + group);
              if (!part) break;
              parts.push(part);
              position += group;
            }
            let formatted = parts.join("-");
            const separatorPoints = groups.slice(0, -1).reduce((points, group) => {
              points.push((points.at(-1) || 0) + group);
              return points;
            }, []);
            if (separatorPoints.includes(digits.length)) formatted += "-";
            return formatted;
          };
          const formatExpiry = (value) => {
            const digits = value.replace(/\\D/g, "").slice(0, 4);
            return digits.length >= 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
          };

          const installMask = (label, formatter) => {
            const input = documentRoot.querySelector(`input[aria-label="${label}"]`);
            if (!input || input.dataset.aqMaskInstalled) return Boolean(input);
            input.dataset.aqMaskInstalled = "true";
            input.addEventListener("input", () => {
              const formatted = formatter(input.value);
              if (formatted !== input.value) setValue(input, formatted);
            });
            return true;
          };

          let attempts = 0;
          const install = () => {
            const cardReady = installMask("Card number", formatCard);
            const expiryReady = installMask("Expiry date", formatExpiry);
            if ((!cardReady || !expiryReady) && attempts++ < 20) setTimeout(install, 100);
          };
          install();
        })();
        </script>
        """,
        height=0,
    )


def _payment_details_from_state(method):
    if method == "Credit / Debit Card":
        return {
            "card_name": st.session_state.get("payment_card_name", ""),
            "card_number": st.session_state.get("payment_card_number", ""),
            "expiry": st.session_state.get("payment_card_expiry", ""),
            "cvv": st.session_state.get("payment_card_cvv", ""),
        }
    if method == "Online Banking (FPX)":
        return {
            "bank": st.session_state.get("payment_bank"),
            "account_name": st.session_state.get("payment_account_name", ""),
        }
    if method == "DuitNow QR":
        return {
            "mobile": st.session_state.get("payment_duitnow_mobile", ""),
        }
    return {
        "wallet": st.session_state.get("payment_wallet"),
        "mobile": st.session_state.get("payment_wallet_mobile", ""),
    }


def _submit_payment(cart, collection_point_id):
    method = st.session_state.get("payment_method", PAYMENT_METHODS[0])
    if method == "Credit / Debit Card":
        _format_card_number()
        _format_expiry_date()
    details = _payment_details_from_state(method)
    errors = validate_payment_details(method, details)
    if collection_point_id is None:
        errors["collection_point"] = "Choose a collection point before payment."
    st.session_state.payment_errors = errors
    if errors:
        return
    ok, message, order_id = complete_demo_payment(
        st.session_state.user_id, cart, method, details, collection_point_id,
    )
    if not ok:
        st.session_state.payment_errors = {"form": message}
        return
    st.session_state.payment_success_pending = order_id


def _clear_collection_point_error():
    """Remove only the collection-point warning as soon as a valid choice is made."""
    errors = dict(st.session_state.get("payment_errors", {}))
    if errors.pop("collection_point", None):
        st.session_state.payment_errors = errors

checkout_cart = st.session_state.get("checkout_cart")
if not checkout_cart:
    st.info("There is no order waiting for payment.")
    st.stop()

summary = checkout_summary(checkout_cart)
if not summary["items"]:
    st.error("The checkout could not be loaded. Please prepare your seafood order again.")
    st.stop()

customer = get_user(st.session_state.user_id) or {}
collection_points = list_collection_points("Available")
if (customer.get("state") or "").strip() == "Perlis":
    collection_points = [point for point in collection_points if point["state"] == "Perlis"]
if not collection_points:
    st.error("No suitable collection point is currently available. Please try again later.")
    st.stop()

point_labels = {
    f"{point['point_name']} · {point['city']}, {point['state']}": point
    for point in collection_points
}
errors = st.session_state.get("payment_errors", {})
left, right = st.columns([1.05, 1], gap="large")

with left:
    with st.container(border=True):
        st.markdown("### Order Summary")
        for line in summary["items"]:
            html = (
                '<div class="aq-checkout-line">'
                f'<div><strong>{line["product_name"]}</strong><br>'
                f'<span style="color:var(--aq-muted)">{line["quantity"]:g} {line["unit"]} × '
                f'RM {line["unit_price"]:,.2f}</span></div>'
                f'<div class="aq-money">RM {line["line_total"]:,.2f}</div>'
                '</div>'
            )
            st.html(html)

        st.write("")
        a, b = st.columns(2)
        a.metric("Total Seafood Weight", f"{summary['total_weight_kg']:g} kg")
        b.metric("Amount to Pay", f"RM {summary['total_amount']:,.2f}")
        selected_point_label = st.selectbox(
            "Collection Point", list(point_labels), index=None,
            placeholder="Select a collection point", key="payment_collection_point",
            on_change=_clear_collection_point_error,
            help="Choose where you will collect your seafood or where AquaLoad will deliver it.",
        )
        selected_point = point_labels.get(selected_point_label)
        if errors.get("collection_point"):
            st.error(errors["collection_point"], icon="⚠️")
        elif not selected_point:
            st.caption("Required before payment. Choose a collection point for this order.")
        elif selected_point["state"] == "Perlis":
            st.info(
                f"Self-pickup: collect at {selected_point['point_name']}. "
                "This order will not be sent to lorry loading."
            )
        else:
            st.info(f"Lorry delivery will be arranged to {selected_point['point_name']} after staff confirmation.")

with right:
    method = st.radio("Choose Payment Method", PAYMENT_METHODS, key="payment_method")
    with st.container(border=True):
        st.markdown("### Payment Details")
        if method == "Credit / Debit Card":
            st.text_input(
                "Card number", placeholder="4242-4242-4242-4242", max_chars=23,
                key="payment_card_number", on_change=_format_card_number,
            )
            _field_feedback(errors, "card_number", "Visa/Mastercard: 16 digits. American Express: 15 digits. Hyphens are added automatically.")
            st.text_input("Cardholder name", placeholder="Name shown on card", key="payment_card_name")
            _field_feedback(errors, "card_name", "Required. Enter the cardholder name.")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input(
                    "Expiry date", placeholder="MM/YY, e.g. 11/27", max_chars=5,
                    key="payment_card_expiry", on_change=_format_expiry_date,
                )
                _field_feedback(errors, "expiry", "Required. The slash is added automatically after MM.")
            with c2:
                st.text_input("CVV", type="password", placeholder="123", max_chars=4, key="payment_card_cvv")
                _field_feedback(errors, "cvv", "Required. Enter the 3 or 4 digit security code.")
            _render_card_input_masks()
        elif method == "Online Banking (FPX)":
            st.selectbox(
                "Bank", MALAYSIAN_BANKS, index=None,
                placeholder="Select your bank", key="payment_bank",
            )
            _field_feedback(errors, "bank", "Choose your Malaysian bank for this simulated FPX transfer.")
            st.text_input("Account holder name", placeholder="Name registered with the bank", key="payment_account_name")
            _field_feedback(errors, "account_name", "Required. Enter the account holder's name.")
        elif method == "DuitNow QR":
            st.text_input("DuitNow mobile number", placeholder="0123456789", key="payment_duitnow_mobile")
            _field_feedback(errors, "mobile", "Required. Enter a Malaysian mobile number.")
        else:
            st.selectbox(
                "E-wallet", MALAYSIAN_EWALLETS, index=None,
                placeholder="Select an e-wallet", key="payment_wallet",
            )
            _field_feedback(errors, "wallet", "Choose a supported Malaysian e-wallet.")
            st.text_input("Mobile number linked to e-wallet", placeholder="0123456789", key="payment_wallet_mobile")
            _field_feedback(errors, "mobile", "Required. Enter the linked Malaysian mobile number.")
        st.divider()
        st.markdown(f"### RM {summary['total_amount']:,.2f}")
        if errors.get("form"):
            st.error(errors["form"], icon="⚠️")
        st.button(
            "Pay & Place Order", type="primary", use_container_width=True,
            on_click=_submit_payment,
            args=(checkout_cart, selected_point["collection_point_id"] if selected_point else None),
        )

if order_id := st.session_state.pop("payment_success_pending", None):
    st.session_state.last_paid_order_id = order_id
    st.session_state.checkout_cart = None
    st.session_state.cart = {}
    st.session_state.pop("payment_errors", None)
    st.switch_page("pages/payment_success.py")

st.stop()

with right:
    with st.container(border=True):
        st.markdown("### Payment Method")
        method = st.radio("Choose Payment Method", PAYMENT_METHODS)

        card_ok = True
        if method == "Credit / Debit Card":
            st.markdown("#### Card Information")
            card_name = st.text_input("Cardholder Name", placeholder="Name shown on card")
            card_number = st.text_input("Card Number", placeholder="1234 5678 9012 3456", max_chars=19)
            c1, c2 = st.columns(2)
            with c1:
                expiry = st.text_input("Expiry Date", placeholder="MM/YY", max_chars=5)
            with c2:
                cvv = st.text_input("CVV", type="password", placeholder="123", max_chars=4)

            digits = re.sub(r"\D", "", card_number)
            card_ok = (
                bool(card_name.strip())
                and len(digits) >= 12
                and bool(re.fullmatch(r"\d{2}/\d{2}", expiry.strip()))
                and cvv.isdigit()
                and len(cvv) in {3, 4}
            )

        elif method == "Online Banking":
            bank = st.selectbox(
                "Bank",
                ["Maybank2u", "CIMB Clicks", "Public Bank", "RHB Now", "Hong Leong Connect", "Bank Islam"],
            )
            st.info(f"{bank} selected.")

        else:
            wallet = st.selectbox("E-Wallet", ["Touch 'n Go eWallet", "GrabPay", "Boost"])
            st.info(f"{wallet} selected.")

        st.divider()
        st.markdown(f"### RM {summary['total_amount']:,.2f}")
        st.caption(
            "This payment interface demonstrates the intended checkout flow. No external payment gateway or real charge is used."
        )

        if st.button("Pay & Place Order", type="primary", use_container_width=True):
            if method == "Credit / Debit Card" and not card_ok:
                st.error("Please complete the card information before continuing.")
            else:
                ok, message, order_id = complete_demo_payment(
                    st.session_state.user_id,
                    checkout_cart,
                    method,
                )
                if ok:
                    st.session_state.last_paid_order_id = order_id
                    st.session_state.checkout_cart = None
                    st.session_state.cart = {}
                    st.switch_page("pages/payment_success.py")
                else:
                    st.error(message)

st.write("")
if st.button("← Back to Order Seafood"):
    st.switch_page("pages/order_seafood.py")
