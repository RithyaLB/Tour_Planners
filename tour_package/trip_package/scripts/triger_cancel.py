# Inside views.py
from ..views import get_cert_fingerprint, call_flight_service

url = "https://192.168.161.64"

content = {
    "flight_id": 42,
    "flight_date": "2025-08-30",
    "reason": "Weather-related cancellations"
}

flight_options = call_flight_service(content, f"{url}/flights/cancel")
