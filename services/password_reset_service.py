"""Secure password-reset OTP lifecycle backed by Supabase PostgreSQL."""

import hashlib
import hmac
import os
import secrets

from database.db import db_session
from database.schema import initialize_schema
from services.auth_service import hash_password, valid_email, validate_password_strength
from services.email_service import send_password_reset_otp


OTP_TTL_MINUTES = 10
MAX_ATTEMPTS = 5


def _pepper() -> str | None:
    return os.getenv("OTP_PEPPER")


def _digest(value: str, pepper: str) -> str:
    return hmac.new(pepper.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def request_password_reset_otp(email: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not valid_email(email):
        return False, "Enter a valid email address."
    pepper = _pepper()
    if not pepper:
        return False, "Email recovery is not configured yet."
    initialize_schema()
    with db_session() as conn:
        user = conn.execute(
            "SELECT user_id, email FROM users WHERE LOWER(email)=LOWER(?) AND status='Active'", (email,)
        ).fetchone()
        if not user:
            return True, "If the email belongs to an active AquaLoad account, a one-time passcode has been sent."
        code = f"{secrets.randbelow(1_000_000):06d}"
        conn.execute("DELETE FROM password_reset_otps WHERE user_id=? AND consumed_at IS NULL", (user["user_id"],))
        conn.execute(
            """
            INSERT INTO password_reset_otps(user_id, otp_hash, expires_at)
            VALUES (?, ?, CURRENT_TIMESTAMP + INTERVAL '10 minutes')
            """,
            (user["user_id"], _digest(code, pepper)),
        )
    delivered, message = send_password_reset_otp(user["email"], code)
    if not delivered:
        with db_session() as conn:
            conn.execute("DELETE FROM password_reset_otps WHERE user_id=? AND consumed_at IS NULL", (user["user_id"],))
    return delivered, message


def verify_password_reset_otp(email: str, code: str) -> tuple[bool, str, str | None]:
    pepper = _pepper()
    if not pepper or not (code or "").isdigit() or len(code) != 6:
        return False, "Enter the six-digit passcode from your email.", None
    initialize_schema()
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT o.*, u.email FROM password_reset_otps o
            JOIN users u ON u.user_id=o.user_id
            WHERE LOWER(u.email)=LOWER(?) AND o.consumed_at IS NULL
            ORDER BY o.created_at DESC LIMIT 1 FOR UPDATE
            """,
            (email.strip(),),
        ).fetchone()
        if not row or row["attempts"] >= MAX_ATTEMPTS:
            return False, "This passcode is invalid or has expired. Request a new code.", None
        valid = hmac.compare_digest(row["otp_hash"], _digest(code, pepper))
        if not valid:
            conn.execute("UPDATE password_reset_otps SET attempts=attempts+1 WHERE reset_id=?", (row["reset_id"],))
            return False, "This passcode is invalid or has expired. Request a new code.", None
        token = secrets.token_urlsafe(32)
        conn.execute(
            """
            UPDATE password_reset_otps
            SET verified_at=CURRENT_TIMESTAMP, verification_token_hash=?
            WHERE reset_id=? AND expires_at>CURRENT_TIMESTAMP
            """,
            (_digest(token, pepper), row["reset_id"]),
        )
        return True, "Email verified. You can now set a new password.", token


def complete_password_reset(email: str, verification_token: str, new_password: str) -> tuple[bool, str]:
    valid, message = validate_password_strength(new_password)
    if not valid:
        return False, message
    pepper = _pepper()
    if not pepper or not verification_token:
        return False, "Your password-reset session has expired. Request a new code."
    initialize_schema()
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT o.reset_id, o.user_id FROM password_reset_otps o
            JOIN users u ON u.user_id=o.user_id
            WHERE LOWER(u.email)=LOWER(?) AND o.consumed_at IS NULL AND o.verified_at IS NOT NULL
              AND o.expires_at>CURRENT_TIMESTAMP AND o.verification_token_hash=?
            ORDER BY o.created_at DESC LIMIT 1 FOR UPDATE
            """,
            (email.strip(), _digest(verification_token, pepper)),
        ).fetchone()
        if not row:
            return False, "Your password-reset session has expired. Request a new code."
        salt, password_hash = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash=?, password_salt=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
            (password_hash, salt, row["user_id"]),
        )
        conn.execute("UPDATE password_reset_otps SET consumed_at=CURRENT_TIMESTAMP WHERE reset_id=?", (row["reset_id"],))
    return True, "Your password has been reset successfully. You can now sign in."
