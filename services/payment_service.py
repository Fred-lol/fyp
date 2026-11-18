from datetime import datetime
import re

from database.db import db_session
from database.schema import initialize_schema
from services.order_service import list_products, place_order


PAYMENT_METHODS = [
    "Credit / Debit Card",
    "Online Banking (FPX)",
    "DuitNow QR",
    "E-Wallet",
]

MALAYSIAN_BANKS = [
    "Maybank2u", "CIMB Clicks", "Public Bank", "RHB", "Hong Leong Connect",
    "Bank Islam", "AmBank", "Bank Rakyat", "BSN", "UOB Malaysia",
]
MALAYSIAN_EWALLETS = [
    "Touch 'n Go eWallet", "GrabPay", "Boost", "ShopeePay", "MAE",
]


def _valid_luhn(number):
    total = 0
    for index, digit in enumerate(reversed(number)):
        value = int(digit)
        if index % 2:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _valid_malaysian_mobile(value):
    digits = re.sub(r"[\s-]", "", str(value or ""))
    return bool(re.fullmatch(r"(?:\+?60|0)1\d{7,9}", digits))


def _malaysian_card_format_error(digits):
    """Validate card schemes commonly issued by Malaysian retail banks."""
    if digits.startswith(("34", "37")):
        if len(digits) != 15:
            return "American Express card numbers must contain 15 digits."
        return None
    if digits.startswith("4") or re.fullmatch(r"5[1-5]\d*|2(?:2[2-9]\d*|[3-6]\d*|7(?:[01]\d*|2[0-1]\d*))", digits):
        if len(digits) != 16:
            return "Visa and Mastercard numbers must contain 16 digits."
        return None
    return "Use a Visa, Mastercard, or American Express card issued by your bank."


def validate_payment_details(payment_method, details):
    """Validate demo-only details; no payment credentials are persisted."""
    details = details or {}
    errors = {}
    if payment_method not in PAYMENT_METHODS:
        return {"form": "Choose a valid payment method."}

    if payment_method == "Credit / Debit Card":
        name = str(details.get("card_name") or "").strip()
        card_number = str(details.get("card_number") or "").strip()
        digits = re.sub(r"\D", "", card_number)
        expiry = str(details.get("expiry") or "").strip()
        cvv = str(details.get("cvv") or "").strip()
        if not name:
            errors["card_name"] = "Cardholder name is required."
        elif len(name) < 2 or not re.search(r"[A-Za-z]", name):
            errors["card_name"] = "Use at least 2 letters for the cardholder name."
        if not card_number:
            errors["card_number"] = "Card number is required."
        elif not re.fullmatch(r"[\d\s-]+", card_number):
            errors["card_number"] = "Card number can contain digits only."
        elif format_error := _malaysian_card_format_error(digits):
            errors["card_number"] = format_error
        elif not _valid_luhn(digits):
            errors["card_number"] = "Check the card number and try again."
        format_match = re.fullmatch(r"(\d{2})/(\d{2})", expiry)
        if not expiry:
            errors["expiry"] = "Expiry date is required."
        elif not format_match:
            errors["expiry"] = "Expiry date must use MM/YY, for example 11/27."
        else:
            expiry_month = int(format_match.group(1))
            if not 1 <= expiry_month <= 12:
                errors["expiry"] = "Expiry month must be between 01 and 12."
            else:
                expiry_year = 2000 + int(format_match.group(2))
                now = datetime.now()
                if (expiry_year, expiry_month) < (now.year, now.month):
                    errors["expiry"] = "This card has expired. Use a current card."
        if not cvv:
            errors["cvv"] = "CVV is required."
        elif not re.fullmatch(r"\d{3,4}", cvv):
            errors["cvv"] = "CVV must be 3 or 4 digits."

    elif payment_method == "Online Banking (FPX)":
        if not details.get("bank"):
            errors["bank"] = "Choose your bank to continue."
        elif details.get("bank") not in MALAYSIAN_BANKS:
            errors["bank"] = "Choose a supported Malaysian bank."
        name = str(details.get("account_name") or "").strip()
        if not name:
            errors["account_name"] = "Account holder name is required."
        elif len(name) < 2 or not re.search(r"[A-Za-z]", name):
            errors["account_name"] = "Use at least 2 letters for the account holder name."

    elif payment_method == "DuitNow QR":
        if not str(details.get("mobile") or "").strip():
            errors["mobile"] = "DuitNow mobile number is required."
        elif not _valid_malaysian_mobile(details.get("mobile")):
            errors["mobile"] = "Enter a Malaysian mobile number, for example 0123456789."

    elif payment_method == "E-Wallet":
        if not details.get("wallet"):
            errors["wallet"] = "Choose an e-wallet to continue."
        elif details.get("wallet") not in MALAYSIAN_EWALLETS:
            errors["wallet"] = "Choose a supported Malaysian e-wallet."
        if not str(details.get("mobile") or "").strip():
            errors["mobile"] = "Mobile number linked to the e-wallet is required."
        elif not _valid_malaysian_mobile(details.get("mobile")):
            errors["mobile"] = "Enter a valid Malaysian mobile number for this e-wallet."
    return errors


def checkout_summary(items):
    """Build a checkout summary from current seafood data without charging anything."""
    initialize_schema()
    clean = [(int(pid), float(qty)) for pid, qty in items if float(qty) > 0]
    product_map = {p["product_id"]: p for p in list_products(availability="All")}
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


def complete_demo_payment(customer_id, items, payment_method, payment_details=None, collection_point_id=None):
    """Simulate a successful payment, then create the AquaLoad Pending order.

    No external payment gateway is called and no card/bank credentials are stored.
    """
    if payment_method not in PAYMENT_METHODS:
        return False, "Please select a valid payment method.", None
    if errors := validate_payment_details(payment_method, payment_details):
        return False, next(iter(errors.values())), None
    if collection_point_id is None:
        return False, "Choose a collection point before payment.", None

    summary = checkout_summary(items)
    if not summary["items"]:
        return False, "Your checkout is empty.", None

    ok, message, order_id = place_order(customer_id, items, collection_point_id=collection_point_id)
    if not ok:
        return False, message, None

    reference = f"AQPAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{order_id}"
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO payments(
                order_id, customer_id, amount, payment_method,
                payment_status, transaction_reference
            ) VALUES(?,?,?,?,?,?)
            """,
            (
                order_id,
                customer_id,
                float(summary["total_amount"]),
                payment_method,
                "Paid",
                reference,
            ),
        )

    return True, "Payment successful and order placed.", order_id


def get_payment(order_id):
    initialize_schema()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
    return dict(row) if row else None
