"""Customer checkout: collection selection and credential-free demo methods."""
import sys
from html import escape
from pathlib import Path
from uuid import uuid4
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
from bootstrap import bootstrap_app
from components.cards import empty_cart
from components.payment_input_guard import numeric_payment_input_guard
from components.theme import apply_theme, page_header
from components.navigation import customer_sidebar
from services.payment_service import (MALAYSIAN_BANKS, MALAYSIAN_EWALLETS, PAYMENT_METHODS,
    checkout_summary, complete_demo_payment, validate_payment_details)
from services.collection_point_service import list_collection_points
from services.auth_service import get_user

bootstrap_app()
st.set_page_config(page_title="Checkout | AquaLoad", page_icon="AquaLoad.png", layout="wide")
apply_theme()
customer_sidebar()
page_header("Review & place your order", "Choose your collection point and complete a demo checkout. No money will be charged.", "Customer checkout", back_target="pages/order_seafood.py")
st.html("""<style>
.st-key-checkout_summary,.st-key-checkout_payment{padding:24px!important;background:var(--aq-card)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important}
.st-key-checkout_payment [data-testid="stForm"]{border:0!important;background:transparent!important;padding:0!important;box-shadow:none!important}
.st-key-payment_method_choices [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:12px!important}
.st-key-payment_method_choices [data-testid="column"]{width:auto!important;min-width:0!important;flex:initial!important;box-sizing:border-box!important}
.st-key-checkout_payment .st-key-payment_method_choices [class*="st-key-payment_method_select_"] button{width:100%!important;min-height:88px!important;padding:12px 10px!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;text-align:center!important;white-space:nowrap!important;line-height:1.25!important;background:var(--aq-card2)!important;color:var(--aq-text)!important;border:1px solid var(--aq-border)!important;border-radius:12px!important;box-shadow:none!important}
.st-key-checkout_payment .st-key-payment_method_choices [class*="st-key-payment_method_select_"] button:hover{border-color:var(--aq-teal)!important;transform:translateY(-1px)!important}
.st-key-checkout_payment .st-key-payment_method_choices [class*="st-key-payment_method_select_"] button *{color:inherit!important;white-space:nowrap!important}
.st-key-checkout_payment .st-key-payment_method_choices [class*="st-key-payment_method_select_"] button p{font-size:clamp(.75rem,.9vw,.9rem)!important;line-height:1.25!important;text-align:center!important;margin:0!important}
.aq-checkout-total{display:flex;justify-content:space-between;align-items:baseline;padding:20px 0;color:var(--aq-text)}.aq-checkout-total strong{font-size:24px}
.st-key-payment_method_choices [class*="st-key-payment_method_select_"] button:focus-visible{outline:3px solid var(--aq-cyan)!important;outline-offset:2px!important}
.aq-numeric-error{color:var(--aq-status-danger-text)!important;font-size:.82rem!important;margin-top:.2rem!important}
@media(max-width:600px){.st-key-checkout_summary,.st-key-checkout_payment{padding:16px!important}.aq-checkout-total strong{font-size:21px!important}}
@media(max-width:420px){.st-key-checkout_payment .st-key-payment_method_choices [class*="st-key-payment_method_select_"] button{min-height:82px!important;padding:8px 4px!important}.st-key-checkout_payment .st-key-payment_method_choices [class*="st-key-payment_method_select_"] button p{font-size:.68rem!important}}
</style>""")


def field_error(errors, field):
    if errors.get(field):
        st.error(errors[field])


def sanitize_numeric(value, limit, *, groups=None, slash_after=None):
    """Normalize submitted numeric text and apply display formatting."""
    digits = ''.join(character for character in str(value or '') if character.isascii() and character.isdigit())[:limit]
    if slash_after and len(digits) > slash_after:
        return digits[:slash_after] + '/' + digits[slash_after:]
    if groups:
        return ' '.join(digits[offset:offset + groups] for offset in range(0, len(digits), groups))
    return digits


def submit_demo_order(cart, point_id, method, details, total):
    """Callback runs before rendering, so inline errors appear immediately."""
    if st.session_state.get("checkout_busy"):
        st.session_state.payment_errors = {"form": "Your order is being submitted. Please wait."}
        return
    errors = validate_payment_details(method, details)
    if point_id is None:
        errors['collection_point'] = 'Select a collection point before placing your demo order.'
    st.session_state.payment_errors = errors
    if errors:
        return
    st.session_state.checkout_busy = True
    try:
        ok, message, order_id = complete_demo_payment(
            st.session_state.user_id, cart, method, details, point_id,
            submission_key=st.session_state.checkout_token, expected_total=total,
        )
        if ok:
            st.session_state.payment_success_pending = order_id
        else:
            st.session_state.payment_errors = {'form':message}
    except Exception:
        # Do not expose connection details or discard the idempotency token:
        # retrying after an uncertain response must recover the same order.
        st.session_state.payment_errors = {'form':'Your order could not be submitted. Please try again. Your cart has been kept.'}
    finally:
        st.session_state.checkout_busy = False


def choose_payment_method(method):
    """Select one payment method and clear prior method-specific values."""
    if method != st.session_state.get("payment_method"):
        st.session_state.payment_method = method
        st.session_state.payment_errors = {}
        # Keep payment inputs short-lived in browser-backed session state; a
        # method switch clears old details instead of retaining them hidden.
        for key in (
            'payment_cardholder', 'payment_card_number', 'payment_expiry',
            'payment_cvv', 'payment_bank', 'payment_duitnow_mobile',
            'payment_wallet', 'payment_wallet_mobile',
        ):
            st.session_state.pop(key, None)


def render_payment(cart, point_id, total):
    labels = {
        'Credit / Debit Card': ('card', ':material/credit_card:', 'Credit / Debit Card'),
        'Online Banking (FPX)': ('fpx', ':material/account_balance:', 'FPX Online Banking'),
        'DuitNow Mobile Number': ('duitnow', ':material/phone_iphone:', 'DuitNow Mobile Number'),
        'E-Wallet': ('wallet', ':material/account_balance_wallet:', 'E-Wallet'),
    }
    method = st.session_state.get('payment_method')
    with st.container(key='payment_method_choices'):
        st.markdown('**Choose a demo payment method**')
        # Pair the four card actions in two responsive rows. They are native
        # buttons, so selection is keyboard accessible without visible radios.
        first_row = st.columns(2)
        second_row = st.columns(2)
        for column, payment_method in zip(first_row + second_row, PAYMENT_METHODS):
            slug, icon, label = labels[payment_method]
            with column:
                selected = payment_method == method
                st.button(
                    f'{"✓  " if selected else ""}{label}',
                    key=f'payment_method_select_{slug}',
                    icon=icon,
                    help=f'Select {label}',
                    on_click=choose_payment_method,
                    args=(payment_method,),
                    use_container_width=True,
                    type='primary' if selected else 'secondary',
                )
    # Explicit class selector styles selected as Streamlit's card button itself.
    if method in labels:
        selected_slug = labels[method][0]
        st.html(f'<style>.st-key-checkout_payment .st-key-payment_method_choices .st-key-payment_method_select_{selected_slug} button{{background:color-mix(in srgb,var(--aq-teal) 14%,var(--aq-card))!important;color:var(--aq-navy)!important;border:2px solid var(--aq-teal)!important;box-shadow:0 3px 12px color-mix(in srgb,var(--aq-teal) 12%,transparent)!important}}</style>')
    errors = st.session_state.get('payment_errors', {})
    field_error(errors, 'method')
    if method is None:
        st.info('Choose a payment method to see its required demo information.')
    with st.form('demo_payment_form', border=False):
        details = {}
        if method == 'Credit / Debit Card':
            st.caption('Test cards only. Never enter a real card number or security code. No payment is processed.')
            details['cardholder'] = st.text_input('Cardholder name (test)', placeholder='Test Customer', key='payment_cardholder', autocomplete='off')
            field_error(errors, 'cardholder')
            details['card_number'] = st.text_input('Test card number', placeholder='4242 4242 4242 4242', key='payment_card_number', autocomplete='off', max_chars=19)
            field_error(errors, 'card_number')
            st.caption('Test numbers: Visa 4242 4242 4242 4242 · Mastercard 5555 5555 5555 4444')
            exp_col, cvv_col = st.columns(2)
            with exp_col:
                details['expiry'] = st.text_input('Expiry (MM/YY)', placeholder='MM/YY', max_chars=5, key='payment_expiry', autocomplete='off')
                field_error(errors, 'expiry')
            with cvv_col:
                details['cvv'] = st.text_input('Test CVV', placeholder='123', max_chars=3, type='password', key='payment_cvv', autocomplete='off')
                field_error(errors, 'cvv')
        elif method == 'Online Banking (FPX)':
            details['bank'] = st.selectbox('Malaysian bank', MALAYSIAN_BANKS, index=None, placeholder='Search or select your bank', key='payment_bank')
            field_error(errors, 'bank')
            st.caption('Demo authorization only. Never enter bank login details, passwords, or OTPs.')
        elif method == 'DuitNow Mobile Number':
            details['mobile'] = st.text_input('DuitNow mobile number', placeholder='0123456789 or 01112345678', key='payment_duitnow_mobile', autocomplete='tel', max_chars=11)
            field_error(errors, 'mobile')
            st.caption('011 numbers are supported. This number is used only for demo validation and is not saved.')
        elif method == 'E-Wallet':
            details['wallet'] = st.selectbox('E-wallet provider', MALAYSIAN_EWALLETS, index=None, placeholder='Select your e-wallet', key='payment_wallet')
            field_error(errors, 'wallet')
            details['mobile'] = st.text_input('Mobile number', placeholder='0123456789', key='payment_wallet_mobile', max_chars=11)
            field_error(errors, 'mobile')
        st.html(f'<div class="aq-checkout-total"><span>Demo order total</span><strong>RM {total:,.2f}</strong></div>')
        field_error(errors, 'form')
        submitted = st.form_submit_button('Place Demo Order', type='primary', width='stretch', disabled=st.session_state.get('checkout_busy', False))
    st.iframe(numeric_payment_input_guard(), width=1, height=1)
    if submitted:
        if method == 'Credit / Debit Card':
            details['card_number'] = sanitize_numeric(details.get('card_number'), 16, groups=4)
            details['expiry'] = sanitize_numeric(details.get('expiry'), 4, slash_after=2)
            details['cvv'] = sanitize_numeric(details.get('cvv'), 3)
        elif method in {'DuitNow Mobile Number', 'E-Wallet'}:
            details['mobile'] = sanitize_numeric(details.get('mobile'), 11)
        submit_demo_order(cart, point_id, method, details, total)
        st.rerun()


cart = st.session_state.get('checkout_cart')
if not cart:
    empty_cart(checkout=True)
    st.stop()
# Keep display-only data within this customer's session. Method changes do not
# fetch products/images again. Submission always validates fresh locked records.
fingerprint = (st.session_state.user_id, tuple((int(pid),float(qty)) for pid,qty in cart))
if st.session_state.get('checkout_fingerprint') != fingerprint:
    st.session_state.checkout_fingerprint = fingerprint
    st.session_state.checkout_token = str(uuid4())
    st.session_state.checkout_snapshot = checkout_summary(cart)
    customer = get_user(st.session_state.user_id) or {}
    points = list_collection_points('Available')
    if (customer.get('state') or '').strip() == 'Perlis':
        points = [point for point in points if point['state'] == 'Perlis']
    st.session_state.checkout_points = points
    st.session_state.payment_errors = {}
summary = st.session_state.checkout_snapshot
if not summary['items']:
    st.error('Your cart is no longer available. Return to the catalogue to choose seafood.')
    st.stop()
if order_id := st.session_state.pop('payment_success_pending', None):
    st.session_state.last_paid_order_id = order_id
    st.session_state.checkout_cart = None
    st.session_state.cart = {}
    for key in ('checkout_fingerprint','checkout_snapshot','checkout_points','payment_errors'):
        st.session_state.pop(key,None)
    for key in ('payment_cardholder','payment_card_number','payment_expiry','payment_cvv','payment_wallet_mobile','payment_duitnow_mobile'):
        st.session_state.pop(key,None)
    st.switch_page('pages/payment_success.py')
    st.stop()
points = st.session_state.checkout_points
point_map = {p['collection_point_id']:p for p in points}
left, right = st.columns([1,1], gap='large')
with left:
    with st.container(key='checkout_summary'):
        st.subheader('Your order', anchor=False)
        for line in summary['items']:
            st.html(f'<div class="aq-checkout-line"><div><strong>{escape(line["product_name"])}</strong><br><small>{line["quantity"]:g} kg &times; RM {line["unit_price"]:,.2f} / kg</small></div><strong>RM {line["line_total"]:,.2f}</strong></div>')
        st.html(f'<div class="aq-checkout-total"><span>{summary["total_weight_kg"]:g} kg total</span><strong>RM {summary["total_amount"]:,.2f}</strong></div>')
        point_id = st.selectbox('Collection point', list(point_map), index=None, placeholder='Select your collection point', key='payment_point_id', format_func=lambda pid: f'{point_map[pid]["point_name"]} - {point_map[pid]["state"]}')
        field_error(st.session_state.get('payment_errors',{}), 'collection_point')
        if not points:
            st.error('No collection points are available. Please try again later.')
        if point_id in point_map:
            point = point_map[point_id]
            st.info(f'Self-pickup at {point["point_name"]}. No lorry delivery is needed.' if point['state']=='Perlis' else f'Collect at {point["point_name"]}. Staff will arrange delivery to this collection point.')
with right:
    with st.container(key='checkout_payment'):
        render_payment(cart, point_id, summary['total_amount'])
