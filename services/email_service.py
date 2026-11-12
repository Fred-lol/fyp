"""Transactional email delivery through Resend. Credentials remain in .env."""

import os

import requests


RESEND_ENDPOINT = "https://api.resend.com/emails"


def send_password_reset_otp(recipient: str, code: str) -> tuple[bool, str]:
    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("OTP_FROM_EMAIL")
    if not api_key or not sender:
        return False, "Email recovery is not configured yet."

    payload = {
        "from": sender,
        "to": [recipient],
        "subject": "Your AquaLoad password reset code",
        "html": (
            "<div style='font-family:Arial,sans-serif;color:#073b63;max-width:520px'>"
            "<h2>AquaLoad password reset</h2>"
            "<p>Use this one-time passcode to reset your password:</p>"
            f"<div style='font-size:30px;letter-spacing:7px;font-weight:700;padding:16px 0'>{code}</div>"
            "<p>This code expires in 10 minutes. Do not share it with anyone.</p>"
            "</div>"
        ),
    }
    try:
        response = requests.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if response.ok:
            return True, "A one-time passcode has been sent if the email belongs to an active AquaLoad account."
        # Keep Resend's raw response private, but provide a useful action for
        # the AquaLoad administrator while configuring email delivery.
        if response.status_code == 401:
            return False, "The email service API key is invalid. Create a new Resend API key and update RESEND_API_KEY."
        if response.status_code == 403:
            return False, "The sender email is not authorized. Verify the email or domain used in OTP_FROM_EMAIL in Resend."
        if response.status_code == 422:
            return False, "The sender or recipient email address is not accepted by the email service. Check OTP_FROM_EMAIL and Resend verification."
        if response.status_code == 429:
            return False, "The email service rate limit has been reached. Please wait a few minutes and try again."
        return False, "The email service rejected this request. Check the delivery log in your Resend dashboard."
    except requests.Timeout:
        return False, "The email service took too long to respond. Check your internet connection and try again."
    except requests.RequestException:
        return False, "AquaLoad could not reach the email service. Check your internet connection and try again."
