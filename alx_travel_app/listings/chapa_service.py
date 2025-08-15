#chapa service helper
# This module provides helper functions for interacting with the Chapa payment gateway.

import requests
from django.conf import settings

class ChapaService:

    @staticmethod
    def initiate_payment(email, amount, first_name, last_name, tx_ref, callback_url):
        url = f"{settings.CHAPA_BASE_URL}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "amount": amount,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": callback_url
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    @staticmethod
    def verify_payment(transaction_id):
        url = f"{settings.CHAPA_BASE_URL}/transaction/verify/{transaction_id}"
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        return response.json()
