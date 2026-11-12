import os
import requests

TRACKING_API_BASE = os.getenv("AQUALOAD_TRACKING_API", "http://127.0.0.1:8000")


def get_order_tracking(order_id, customer_id):
    try:
        response = requests.get(
            f"{TRACKING_API_BASE}/api/orders/{int(order_id)}/tracking",
            params={"customer_id": int(customer_id)},
            timeout=4,
        )
        if response.status_code == 200:
            return True, response.json()
        if response.status_code == 404:
            return False, "Tracking data for this order could not be found."
        return False, "The AquaLoad tracking service returned an error."
    except requests.RequestException:
        return False, "Live tracking service is not running. Start tracking_api.py to view the lorry location."
