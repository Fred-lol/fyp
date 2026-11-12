import hashlib
import hmac
import os
import re

from database.db import db_session
from database.schema import initialize_schema
from constants import ROLES, STAFF_ROLES, THEME_PREFERENCES, MALAYSIA_STATES


def hash_password(password: str):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex(), digest.hex()


def validate_password_strength(password: str):
    """Validate the password policy used by registration and password changes."""
    requirements = password_requirement_status(password)
    missing = [
        label
        for key, label in (
            ("minimum_length", "at least 8 characters"),
            ("uppercase_letter", "at least 1 uppercase letter"),
            ("special_character", "at least 1 special character"),
        )
        if not requirements[key]
    ]
    if missing:
        return False, "Password must include " + ", ".join(missing) + "."
    return True, ""


def password_requirement_status(password: str):
    """Return individual password-rule results for live form feedback."""
    return {
        "minimum_length": len(password) >= 8,
        "uppercase_letter": bool(re.search(r"[A-Z]", password)),
        "special_character": bool(re.search(r"[^A-Za-z0-9]", password)),
    }


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return hmac.compare_digest(digest.hex(), hash_hex)


def valid_email(email: str) -> bool:
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email.strip()) is not None


def valid_phone(phone: str) -> bool:
    cleaned = re.sub(r"[\s\-()]", "", phone)
    return re.match(r"^\+?[0-9]{9,15}$", cleaned) is not None


def is_staff_style_email(email: str) -> bool:
    email = email.strip().lower()
    return "@" in email and ".aquaload" in email.split("@", 1)[0]


def create_user(
    full_name,
    email,
    phone_number,
    password,
    role=ROLES["CUSTOMER"],
    status="Active",
    ignore_existing=False,
    address="",
    city="",
    state="",
    postcode="",
    latitude=None,
    longitude=None,
):
    initialize_schema()
    email = email.strip().lower()
    salt, pw_hash = hash_password(password)
    try:
        with db_session() as conn:
            cur = conn.execute(
                """
                INSERT INTO users(
                    full_name,email,phone_number,address,city,state,postcode,
                    latitude,longitude,password_hash,password_salt,role,status
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    full_name.strip(), email, phone_number.strip(), address.strip(),
                    city.strip(), state.strip(), postcode.strip(), latitude, longitude,
                    pw_hash, salt, role, status,
                ),
            )
            return cur.lastrowid
    except Exception as exc:
        if ignore_existing and "UNIQUE constraint failed" in str(exc):
            return None
        raise


def register_customer(full_name, email, phone_number, address, city, state, postcode, password):
    if not full_name.strip():
        return False, "Please enter your full name."
    if not valid_email(email):
        return False, "Please enter a valid email address."
    if is_staff_style_email(email):
        return False, "AquaLoad staff accounts cannot be created through customer registration."
    if not valid_phone(phone_number):
        return False, "Please enter a valid phone number."
    if not city.strip():
        return False, "Please enter your city."
    if state not in MALAYSIA_STATES:
        return False, "Please select your Malaysian state or federal territory."
    if not postcode.strip() or not re.match(r"^\d{5}$", postcode.strip()):
        return False, "Please enter a valid 5-digit Malaysian postcode."
    password_valid, password_error = validate_password_strength(password)
    if not password_valid:
        return False, password_error

    initialize_schema()
    with db_session() as conn:
        if conn.execute("SELECT 1 FROM users WHERE LOWER(email)=LOWER(?)", (email.strip(),)).fetchone():
            return False, "An account with this email address already exists."
    try:
        create_user(
            full_name, email, phone_number, password, role=ROLES["CUSTOMER"],
            address=address, city=city, state=state, postcode=postcode,
        )
        return True, "Your AquaLoad account has been created successfully."
    except Exception:
        return False, "Unable to create the account. Please try again."


def authenticate_user(email: str, password: str):
    initialize_schema()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE LOWER(email)=LOWER(?)", (email.strip(),)).fetchone()
    if not row:
        return None, "Incorrect email or password."
    if row["status"] != "Active":
        return None, "This account is currently inactive."
    if not verify_password(password, row["password_salt"], row["password_hash"]):
        return None, "Incorrect email or password."
    return dict(row), None


def get_user(user_id):
    initialize_schema()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_profile(user_id, full_name, phone_number, address="", city="", state="", postcode=""):
    if not full_name.strip():
        return False, "Full name is required."
    if not valid_phone(phone_number):
        return False, "Please enter a valid phone number."
    if not city.strip() or state not in MALAYSIA_STATES:
        return False, "City and state are required."
    if not re.match(r"^\d{5}$", postcode.strip()):
        return False, "Please enter a valid 5-digit Malaysian postcode."
    with db_session() as conn:
        conn.execute(
            """
            UPDATE users
            SET full_name=?, phone_number=?, address=?, city=?, state=?, postcode=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE user_id=?
            """,
            (full_name.strip(), phone_number.strip(), address.strip(), city.strip(), state, postcode.strip(), user_id),
        )
    return True, "Profile updated successfully. Future orders will use your latest location for collection-point assignment."


def change_password(user_id, current_password, new_password):
    user = get_user(user_id)
    if not user:
        return False, "User account could not be found."
    if not verify_password(current_password, user["password_salt"], user["password_hash"]):
        return False, "Current password is incorrect."
    password_valid, password_error = validate_password_strength(new_password)
    if not password_valid:
        return False, password_error
    salt, pw_hash = hash_password(new_password)
    with db_session() as conn:
        conn.execute(
            "UPDATE users SET password_hash=?, password_salt=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (pw_hash, salt, user_id),
        )
    return True, "Password changed successfully."


def update_theme_preference(user_id, preference):
    preference = (preference or "System").title()
    if preference not in THEME_PREFERENCES:
        return False, "Invalid appearance preference."
    with db_session() as conn:
        conn.execute(
            "UPDATE users SET theme_preference=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (preference, user_id),
        )
    return True, "Appearance preference saved successfully."


def reset_password_with_phone(email, phone_number, new_password):
    password_valid, password_error = validate_password_strength(new_password)
    if not password_valid:
        return False, password_error
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(?) AND phone_number=? AND status='Active'",
            (email.strip(), phone_number.strip()),
        ).fetchone()
        if not row:
            return False, "The email and phone number do not match an active account."
        salt, pw_hash = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash=?, password_salt=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (pw_hash, salt, row["user_id"]),
        )
    return True, "Password reset successfully."


def is_staff_role(role):
    return role in STAFF_ROLES


def email_exists(email):
    initialize_schema()
    with db_session() as conn:
        return conn.execute("SELECT 1 FROM users WHERE LOWER(email)=LOWER(?)", (email.strip(),)).fetchone() is not None
