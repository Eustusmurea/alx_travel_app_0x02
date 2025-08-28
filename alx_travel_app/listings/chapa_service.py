# chapa_service.py
import os
import uuid
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY", getattr(settings, "CHAPA_SECRET_KEY", ""))
CHAPA_BASE_URL = os.getenv("CHAPA_BASE_URL", getattr(settings, "CHAPA_BASE_URL", "https://api.chapa.co/v1"))

if not CHAPA_SECRET_KEY:
    raise ValueError("CHAPA_SECRET_KEY must be set in environment or settings.py")

HEADERS = {
    "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
    "Content-Type": "application/json"
}

def initialize_payment(amount, email, tx_ref=None, currency="ETB", first_name="", last_name="", callback_url=None):
    """
    Initialize a Chapa payment
    """
    if not tx_ref:
        tx_ref = str(uuid.uuid4())  # Generate unique tx_ref if not provided

    # Use ngrok URL for callback_url and return_url
    if callback_url is None:
        callback_url = getattr(settings, "NGROK_URL", "https://5af3e1a557cc.ngrok-free.app") + "/api/payments/webhook/"
    return_url = getattr(settings, "NGROK_URL", "https://5af3e1a557cc.ngrok-free.app") + "/api/payments/return/"

    payload = {
        "amount": str(amount),  # Must be string
        "currency": currency,
        "email": email,
        "tx_ref": tx_ref,
        "first_name": first_name,
        "last_name": last_name,
        "callback_url": callback_url,
        "return_url": return_url
    }

    try:
        response = requests.post(
            f"{CHAPA_BASE_URL}/transaction/initialize",
            headers=HEADERS,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        data["data"]["tx_ref"] = tx_ref  # Include tx_ref for local tracking
        return data
    except requests.Timeout:
        logger.error("Chapa initialize_payment request timed out")
        return {"status": "error", "message": "Request timed out"}
    except requests.RequestException as e:
        logger.error(f"Chapa initialize_payment error: {e}")
        return {"status": "error", "message": str(e)}

def verify_payment(tx_ref):
    """
    Verify the status of a Chapa payment
    """
    try:
        response = requests.get(
            f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logger.error("Chapa verify_payment request timed out")
        return {"status": "error", "message": "Request timed out"}
    except requests.RequestException as e:
        logger.error(f"Chapa verify_payment error: {e}")
        return {"status": "error", "message": str(e)}