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
.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"]{display:grid!important;grid-template-columns:1fr 1fr;gap:10px!important}
.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"] label{border:1px solid var(--aq-border);padding:16px!important;border-radius:10px;background:var(--aq-card2);margin:0!important;min-width:0;cursor:pointer;min-height:60px;display:flex;align-items:center}
.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){border-color:var(--aq-teal);background:color-mix(in srgb,var(--aq-teal) 10%,var(--aq-card))}
.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"] p{margin:0!important;font-weight:650!important}
.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"] label [data-baseweb="radio"]>div:first-child{position:absolute!important;width:1px!important;height:1px!important;clip-path:inset(50%)!important;overflow:hidden!important}
.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"] label:focus-within{outline:2px solid var(--aq-teal);outline-offset:2px}
.aq-checkout-total{display:flex;justify-content:space-between;align-items:baseline;padding:20px 0;color:var(--aq-text)}.aq-checkout-total strong{font-size:24px}
.aq-demo-qr{padding:20px;border:1px dashed var(--aq-border);border-radius:8px;text-align:center;color:var(--aq-text);background:var(--aq-card2)}.aq-demo-qr svg{display:block;margin:0 auto 12px;width:100px;height:100px;color:var(--aq-teal)}
@media(max-width:600px){.st-key-checkout_summary,.st-key-checkout_payment{padding:16px!important}.st-key-checkout_payment [data-testid="stRadio"] [role="radiogroup"]{grid-template-columns:1fr}}
</style>""")


def field_error(errors, field):
    if errors.get(field):
        st.error(errors[field])


def submit_demo_order(cart, point_id, method, details):
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
        ok, message, order_id = complete_demo_payment(st.session_state.user_id, cart, method, details, point_id,
            submission_key=st.session_state.checkout_token)
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


def render_payment(cart, point_id, total):
    labels = {'Credit / Debit Card':'Credit / Debit Card', 'Online Banking (FPX)':'FPX Online Banking', 'DuitNow QR':'DuitNow QR', 'E-Wallet':'E-Wallet'}
    method = st.radio('Demo payment method', PAYMENT_METHODS, index=None, key='payment_method', format_func=labels.get, horizontal=False)
    errors = st.session_state.get('payment_errors', {})
    field_error(errors, 'method')
    with st.form('demo_payment_form', border=False):
        details = {}
        if method == 'Credit / Debit Card':
            st.caption('Test cards only. Never enter a real card number or security code. No payment is processed.')
            details['cardholder'] = st.text_input('Cardholder name (test)', placeholder='Test Customer', key='payment_cardholder', autocomplete='off')
            field_error(errors, 'cardholder')
            details['card_number'] = st.text_input('Test card number', placeholder='4242 4242 4242 4242', key='payment_card_number', autocomplete='off')
            field_error(errors, 'card_number')
            st.caption('Examples: Visa 4242 4242 4242 4242 · Mastercard 5555 5555 5555 4444 · Amex 3782 822463 10005')
            exp_col, cvv_col = st.columns(2)
            with exp_col:
                details['expiry'] = st.text_input('Expiry (MM/YY)', placeholder='MM/YY', max_chars=5, key='payment_expiry', autocomplete='off')
                field_error(errors, 'expiry')
            with cvv_col:
                details['cvv'] = st.text_input('Test CVV', placeholder='123', max_chars=4, type='password', key='payment_cvv', autocomplete='off')
                field_error(errors, 'cvv')
        elif method == 'Online Banking (FPX)':
            details['bank'] = st.selectbox('Malaysian bank', MALAYSIAN_BANKS, index=None, placeholder='Search or select your bank', key='payment_bank')
            field_error(errors, 'bank')
            st.caption('A real FPX checkout redirects to your bank. This demo does not connect to a bank.')
        elif method == 'DuitNow QR':
            st.html('<div class="aq-demo-qr"><svg viewBox="0 0 100 100" aria-label="Non-scannable demo illustration"><g fill="none" stroke="currentColor" stroke-width="5"><rect x="8" y="8" width="24" height="24"/><rect x="68" y="8" width="24" height="24"/><rect x="8" y="68" width="24" height="24"/><path d="M45 8v20M70 70h22v22M8 48h25M50 70v22"/></g><text x="50" y="56" text-anchor="middle" fill="currentColor" font-size="14">DEMO</text></svg><strong>DEMO &mdash; NOT FOR PAYMENT</strong><p>This illustration cannot be used to pay.</p></div>')
        elif method == 'E-Wallet':
            details['wallet'] = st.selectbox('E-wallet provider', MALAYSIAN_EWALLETS, index=None, placeholder='Select your e-wallet', key='payment_wallet')
            field_error(errors, 'wallet')
            details['mobile'] = st.text_input('Mobile number', placeholder='0123456789', key='payment_wallet_mobile')
            field_error(errors, 'mobile')
        if method:
            details['demo_confirmed'] = st.checkbox('Confirm this demo step - no money will be charged', key='demo_confirmed_'+method)
            field_error(errors, 'demo_confirmed')
        st.html(f'<div class="aq-checkout-total"><span>Demo order total</span><strong>RM {total:,.2f}</strong></div>')
        field_error(errors, 'form')
        submitted = st.form_submit_button('Place Demo Order', type='primary', width='stretch', disabled=st.session_state.get('checkout_busy', False))
    if submitted:
        submit_demo_order(cart, point_id, method, details)
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
    for key in ('payment_cardholder','payment_card_number','payment_expiry','payment_cvv','payment_wallet_mobile'):
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
