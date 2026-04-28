from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_registration_verification_email(*, to_email: str, subject: str, html_body: str, text_body: str) -> None:
    api_key = getattr(settings, "BREVO_API_KEY", "")
    sender_email = getattr(settings, "BREVO_SENDER_EMAIL", "")
    sender_name = getattr(settings, "BREVO_SENDER_NAME", "") or sender_email

    if api_key and sender_email:
        payload = {
            "sender": {"email": sender_email, "name": sender_name},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
            "textContent": text_body,
        }
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers={"accept": "application/json", "content-type": "application/json", "api-key": api_key},
            timeout=30,
        )
        if response.status_code >= 400:
            logger.warning("Brevo API failed %s: %s", response.status_code, response.text[:300])
            response.raise_for_status()
        return

    # Local fallback: console/file backend based on Django EMAIL_BACKEND.
    send_mail(subject=subject, message=text_body, from_email=None, recipient_list=[to_email], fail_silently=False)
