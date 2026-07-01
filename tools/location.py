import math
import re
from typing import Any, Dict, Optional, Tuple

import httpx

DEFAULT_LOCATION = {
    "label": "Bengaluru, Karnataka 560001",
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India",
    "pincode": "560001",
    "source": "fallback",
}

KNOWN_CITY_PINS = {
    "kolkata": "700001",
    "calcutta": "700001",
    "bangalore": "560001",
    "bengaluru": "560001",
    "delhi": "110001",
    "new delhi": "110001",
    "mumbai": "400001",
    "bombay": "400001",
    "chennai": "600001",
    "madras": "600001",
    "hyderabad": "500001",
    "pune": "411001",
    "ahmedabad": "380001",
    "gurgaon": "122001",
    "gurugram": "122001",
    "noida": "201301",
}

KNOWN_CITY_COORDS = {
    "bengaluru": (12.9716, 77.5946, "560001"),
    "delhi": (28.6139, 77.2090, "110001"),
    "mumbai": (19.0760, 72.8777, "400001"),
    "hyderabad": (17.3850, 78.4867, "500001"),
    "chennai": (13.0827, 80.2707, "600001"),
    "pune": (18.5204, 73.8567, "411001"),
    "kolkata": (22.5726, 88.3639, "700001"),
    "ahmedabad": (23.0225, 72.5714, "380001"),
    "gurugram": (28.4595, 77.0266, "122001"),
    "noida": (28.5355, 77.3910, "201301"),
}


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _city_pincode_from_text(text: str) -> Optional[str]:
    clean = text.strip().lower()
    match = re.search(r"\b\d{6}\b", clean)
    if match:
        return match.group(0)

    for city, pin in KNOWN_CITY_PINS.items():
        if city in clean:
            return pin
    return None


def _nearest_known_city_pincode(lat: float, lon: float) -> Optional[str]:
    best: Tuple[float, str] | None = None
    for _, (city_lat, city_lon, pin) in KNOWN_CITY_COORDS.items():
        distance = math.hypot(lat - city_lat, lon - city_lon)
        if best is None or distance < best[0]:
            best = (distance, pin)
    return best[1] if best and best[0] <= 1.2 else None


def reverse_geocode(latitude: float, longitude: float) -> Dict[str, Any]:
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "format": "jsonv2",
                "lat": latitude,
                "lon": longitude,
                "zoom": 18,
                "addressdetails": 1,
            },
            headers={"User-Agent": "OneBuy-local-price-comparison/1.0"},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    address = data.get("address") or {}
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("suburb")
        or address.get("county")
        or ""
    )
    state = address.get("state") or ""
    country = address.get("country") or ""
    pincode = address.get("postcode") or ""

    label_parts = [part for part in [city, state, pincode] if part]
    return {
        "label": ", ".join(label_parts) or data.get("display_name", ""),
        "city": city,
        "state": state,
        "country": country,
        "pincode": pincode,
        "displayName": data.get("display_name", ""),
    }


def normalize_location(raw_location: Any) -> Dict[str, Any]:
    if isinstance(raw_location, dict):
        latitude = _coerce_float(raw_location.get("latitude") or raw_location.get("lat"))
        longitude = _coerce_float(raw_location.get("longitude") or raw_location.get("lng"))
        normalized = {
            "label": raw_location.get("label") or raw_location.get("displayName") or "",
            "city": raw_location.get("city") or "",
            "state": raw_location.get("state") or "",
            "country": raw_location.get("country") or "",
            "pincode": str(
                raw_location.get("deliveryPincode")
                or raw_location.get("delivery_pincode")
                or raw_location.get("pincode")
                or raw_location.get("postcode")
                or ""
            ),
            "detectedPincode": str(raw_location.get("detectedPincode") or raw_location.get("pincode") or raw_location.get("postcode") or ""),
            "deliveryPincode": str(raw_location.get("deliveryPincode") or raw_location.get("delivery_pincode") or ""),
            "source": raw_location.get("source") or "browser",
            "accuracy": raw_location.get("accuracy"),
        }
        if latitude is not None and longitude is not None:
            normalized["latitude"] = latitude
            normalized["longitude"] = longitude
            if not normalized["pincode"]:
                normalized.update({k: v for k, v in reverse_geocode(latitude, longitude).items() if v})
                normalized["detectedPincode"] = normalized.get("pincode", "")
            if not normalized["pincode"]:
                normalized["pincode"] = _nearest_known_city_pincode(latitude, longitude) or ""
                normalized["detectedPincode"] = normalized.get("pincode", "")
        if not normalized["pincode"]:
            normalized["pincode"] = _city_pincode_from_text(normalized["label"]) or ""
        if not normalized["label"]:
            normalized["label"] = format_location_label(normalized)
        return normalized

    if isinstance(raw_location, str):
        pin = _city_pincode_from_text(raw_location) or DEFAULT_LOCATION["pincode"]
        city = raw_location.split(",")[0].strip() if raw_location.strip() else DEFAULT_LOCATION["city"]
        return {
            "label": raw_location.strip() or DEFAULT_LOCATION["label"],
            "city": city,
            "state": "",
            "country": "India",
            "pincode": pin,
            "source": "text",
        }

    return dict(DEFAULT_LOCATION)


def format_location_label(location: Dict[str, Any]) -> str:
    parts = [
        location.get("city") or "",
        location.get("state") or "",
        location.get("pincode") or "",
    ]
    return ", ".join(part for part in parts if part) or DEFAULT_LOCATION["label"]


def pincode_for(location: Any) -> str:
    normalized = normalize_location(location)
    if isinstance(location, dict):
        return normalized.get("pincode") or ""
    return normalized.get("pincode") or DEFAULT_LOCATION["pincode"]


def city_for(location: Any) -> str:
    normalized = normalize_location(location)
    return (normalized.get("city") or normalized.get("label") or DEFAULT_LOCATION["city"]).split(",")[0]
