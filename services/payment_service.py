from datetime import datetime, date
import re

from database.db import db_session
from database.schema import initialize_schema
from services.order_service import place_order


PAYMENT_METHODS = [
    "Credit / Debit Card",
    "Online Banking (FPX)",
    "DuitNow Mobile Number",
    "E-Wallet",
]

# Configurable demo subset of PayNet FPX participating banks (verified 19 Nov 2026).
# https://knowledgebase.paynet.my/hc/en-us/articles/49685463748121-Which-banks-participate-in-FPX
MALAYSIAN_BANKS = [
    "Maybank2u", "CIMB Clicks", "Public Bank", "RHB", "Hong Leong Connect",
    "Bank Islam", "AmBank", "Bank Rakyat", "BSN", "UOB Malaysia",
]
MALAYSIAN_EWALLETS = [
    "Touch 'n Go eWallet", "GrabPay", "Boost", "ShopeePay", "MAE",
]


def _valid_malaysian_mobile(value):
    """MCMC national mobile formats: 011 + 8 digits, other mobile prefixes + 7."""
    number = re.sub(r"[\s-]", "", str(value or ""))
    if number.startswith("+60"):
        number = "0" + number[3:]
    elif number.startswith("60"):
        number = "0" + number[2:]
    return bool(re.fullmatch(r"(?:011[0-9]{8}|01[02346789][0-9]{7})", number))


def validate_payment_details(payment_method, details):
    """Only non-sensitive demo selections are accepted. Never request credentials."""
    details = details or {}
    errors = {}
    if payment_method not in PAYMENT_METHODS:
        return {"method": "Select a demo payment method."}
    if payment_method == "Credit / Debit Card":
        name = str(details.get("cardholder") or "").strip()
        number = re.sub(r"[ -]", "", str(details.get("card_number") or ""))
        expiry = str(details.get("expiry") or "").strip()
        cvv = str(details.get("cvv") or "").strip()
        if not 2 <= len(name) <= 80 or not re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+)*", name):
            errors["cardholder"] = "Enter 2–80 letters and spaces for the cardholder name."
        if not number.isascii() or not number.isdigit() or len(number) != 16:
            errors["card_number"] = "Enter a valid 16-digit test card number."
        match = re.fullmatch(r"(0[1-9]|1[0-2])/([0-9]{2})", expiry)
        if not match:
            errors["expiry"] = "Use a valid expiry in MM/YY format."
        else:
            year, month = 2000 + int(match[2]), int(match[1])
            today = date.today()
            if (year, month) < (today.year, today.month):
                errors["expiry"] = "Use the current month or a future expiry."
        if not re.fullmatch(r"[0-9]{3}", cvv):
            errors["cvv"] = "Enter exactly 3 digits for the test CVV."
    if payment_method == "Online Banking (FPX)" and details.get("bank") not in MALAYSIAN_BANKS:
        errors["bank"] = "Select a supported Malaysian bank."
    if payment_method == "DuitNow Mobile Number":
        if not _valid_malaysian_mobile(details.get("mobile")):
            errors["mobile"] = "Enter a valid Malaysian mobile number, such as 0123456789 or +60123456789. 011 numbers are supported."
    if payment_method == "E-Wallet":
        if details.get("wallet") not in MALAYSIAN_EWALLETS:
            errors["wallet"] = "Select a supported e-wallet provider."
        if not _valid_malaysian_mobile(details.get("mobile")):
            errors["mobile"] = "Enter a Malaysian mobile number: 0123456789 or 01112345678. +60 format is also accepted."
    return errors


def checkout_summary(items):
    """Build a checkout summary from current seafood data without charging anything."""
    initialize_schema()
    clean = [(int(pid), float(qty)) for pid, qty in items if float(qty) > 0]
    ids = list({pid for pid, _ in clean})
    if not ids:
        return {"items": [], "total_weight_kg": 0, "total_amount": 0}
    with db_session() as conn:
        products = conn.execute(
            "SELECT product_id,product_name,unit,unit_price,stock_quantity,availability_status FROM seafood_products WHERE product_id IN (" + ",".join("?" for _ in ids) + ")", ids,
        ).fetchall()
    product_map = {p["product_id"]: p for p in products}
    lines = []
    total_weight = 0.0
    total_amount = 0.0

    for product_id, qty in clean:
        product = product_map.get(product_id)
        if not product:
            continue
        price = float(product.get("unit_price") or 0)
        line_total = qty * price
        lines.append(
            {
                "product_id": product_id,
                "product_name": product["product_name"],
                "quantity": qty,
                "unit": product["unit"],
                "unit_price": price,
                "line_total": line_total,
                "stock_quantity": float(product.get("stock_quantity") or 0),
                "availability_status": product.get("availability_status"),
            }
        )
        if product["unit"] == "kg":
            total_weight += qty
        total_amount += line_total

    return {
        "items": lines,
        "total_weight_kg": round(total_weight, 3),
        "total_amount": round(total_amount, 2),
    }


def complete_demo_payment(customer_id, items, payment_method, payment_details=None, collection_point_id=None, *, submission_key=None, expected_total=None):
    """Atomically reserve stock and record a simulated payment, once per checkout.

    Advisory locking serializes duplicate requests across processes. The unique
    transaction reference persists the result so retries return the same order.
    No financial credentials or mobile numbers are persisted.
    """
    from uuid import UUID
    from hashlib import sha256
    if errors := validate_payment_details(payment_method, payment_details):
        return False, next(iter(errors.values())), None
    if collection_point_id is None:
        return False, "Choose an available collection point.", None
    try:
        token = str(UUID(str(submission_key)))
    except (ValueError, TypeError):
        return False, "This checkout has expired. Return to your cart and try again.", None
    reference = f"AQDEMO-{customer_id}-{token}"
    lock_id = int.from_bytes(sha256(reference.encode()).digest()[:8], 'big', signed=True)
    initialize_schema()
    with db_session() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(?)", (lock_id,))
        existing = conn.execute("SELECT order_id FROM payments WHERE transaction_reference=? AND customer_id=?", (reference, customer_id)).fetchone()
        if existing:
            return True, "This demo order was already submitted. No duplicate was created.", existing['order_id']
        ok, message, order_id = place_order(
            customer_id, items, collection_point_id=collection_point_id,
            _connection=conn, expected_total=expected_total,
        )
        if not ok:
            return False, message, None
        # Products remain locked by place_order; use authoritative prices in the
        # same transaction rather than a potentially stale browser summary.
        amount = conn.execute("""SELECT COALESCE(SUM(oi.quantity * p.unit_price),0) AS amount
            FROM order_items oi JOIN seafood_products p ON p.product_id=oi.product_id
            WHERE oi.order_id=?""", (order_id,)).fetchone()['amount']
        conn.execute("""INSERT INTO payments(order_id,customer_id,amount,payment_method,payment_status,transaction_reference)
            VALUES(?,?,?,?,?,?)""", (order_id, customer_id, round(float(amount), 2), payment_method, "Simulated", reference))
    return True, "Demo order submitted successfully. No money was charged.", order_id


def get_payment(order_id):
    initialize_schema()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
    return dict(row) if row else None
