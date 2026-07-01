import os
import json
import re
from typing import Any, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .base import CommerceItem
from .location import pincode_for


GENERIC_BRAND_WORDS = {
    "a2", "atta", "bread", "brown", "butter", "classic", "fresh", "garlic",
    "gold", "high", "loaf", "milk", "multigrain", "oven", "premium", "pure",
    "sandwich", "sourdough", "the", "white", "whole", "wheat", "zero",
}


def _clean_lines(page_text: str) -> List[str]:
    return [line.strip() for line in page_text.splitlines() if line.strip()]


def _is_delivery_line(line: str) -> bool:
    return bool(re.match(r"^\d+\s*(?:mins?|minutes?|hrs?|hours?)$", line.strip(), re.I))


def _is_pack_line(line: str) -> bool:
    return bool(re.search(r"\b\d+(?:\.\d+)?\s?(?:ml|l|litre|liter|g|gm|kg|pcs|pc|pieces)\b", line, re.I))


def _price_from_line(line: str) -> Optional[float]:
    match = re.search(r"(?:₹|rs\.?)\s*([0-9]+(?:\.[0-9]+)?)", line, re.I)
    return float(match.group(1)) if match else None


def _brand_from_name(name: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9']+", name)
    if len(tokens) >= 3 and tokens[0].lower() == "the":
        return " ".join(tokens[:3])
    if len(tokens) >= 2:
        return " ".join(tokens[:2])

    brand_tokens = []
    for token in tokens:
        clean = token.lower()
        if clean in GENERIC_BRAND_WORDS or clean.isdigit():
            if brand_tokens:
                break
            continue
        brand_tokens.append(token)
        if len(brand_tokens) == 2:
            break
    return " ".join(brand_tokens)


def _fallback_parse_products(store_name: str, query: str, page_text: str, source_url: str = "") -> List[CommerceItem]:
    lines = _clean_lines(page_text)
    query_words = {
        word for word in re.findall(r"[a-z0-9]+", query.lower())
        if len(word) > 2 and word not in {"for", "and", "the"}
    }
    items: List[CommerceItem] = []
    seen = set()

    for index, line in enumerate(lines):
        if not _is_delivery_line(line):
            continue

        name = ""
        pack_size = ""
        prices: List[float] = []

        for candidate in lines[index + 1:index + 8]:
            lower = candidate.lower()
            if lower in {"add", "login", "my cart"} or "off" in lower:
                continue
            price = _price_from_line(candidate)
            if price is not None:
                prices.append(price)
                continue
            if not name and len(candidate) > 3 and not _is_pack_line(candidate):
                name = candidate
                continue
            if name and not pack_size and _is_pack_line(candidate):
                pack_size = candidate
                continue

        if not name or not prices:
            continue

        name_words = set(re.findall(r"[a-z0-9]+", name.lower()))
        if query_words and not query_words.intersection(name_words):
            continue

        final_price = prices[0]
        mrp = prices[-1] if len(prices) > 1 and prices[-1] >= final_price else final_price
        key = (store_name, name.lower(), pack_size.lower(), final_price)
        if key in seen:
            continue
        seen.add(key)

        items.append(
            CommerceItem(
                store=store_name,
                price=mrp,
                delivery_time=line,
                coupons="",
                final_cost=final_price,
                name=name,
                brand=_brand_from_name(name),
                pack_size=pack_size,
                source_url=source_url,
                status="available",
            )
        )

    return items[:12]


def parse_products_with_gemini(store_name: str, query: str, page_text: str, source_url: str = "") -> List[CommerceItem]:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _fallback_parse_products(store_name, query, page_text, source_url)
        
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Analyze the visible text content of a search page on {store_name} for the query "{query}".
    Extract a list of matching products. For each product, extract:
    - Name
    - Brand, if visible or clearly inferable from the product name
    - Pack size or quantity, if visible (examples: "500 ml", "1 L", "6 pcs", "1 kg")
    - Price (number only)
    - Delivery time estimate (e.g., "12 mins", "Tomorrow", "15 mins")
    - Active coupons mentioned (e.g., "FREEDEL" or null if none)

    Return the results ONLY as a valid JSON list of objects matching the schema:
    [
      {{"store": "{store_name}", "price": 12.34, "delivery_time": "12 mins", "coupons": "FREEDEL", "final_cost": 12.34, "name": "Product Name", "brand": "Brand Name", "pack_size": "1 L"}}
    ]
    Prefer exact products that match the requested product type and pack size. Include multiple brands when the query does not specify a brand.
    If a stale location prompt is present but matching products and prices are visible, still extract the products.
    Return an empty list [] only when there are no matching products or the page clearly shows no results/service unavailable without visible matching product rows.

    Page text:
    {page_text[:40000]}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        items = []
        if isinstance(data, list):
            for obj in data:
                price = float(obj.get("price", 0))
                final_cost = float(obj.get("final_cost", price))
                items.append(
                    CommerceItem(
                        store=obj.get("store", store_name),
                        price=price,
                        delivery_time=obj.get("delivery_time", "N/A"),
                        coupons=obj.get("coupons", "") or "",
                        final_cost=final_cost,
                        name=obj.get("name", ""),
                        brand=obj.get("brand", "") or "",
                        pack_size=obj.get("pack_size", "") or "",
                        source_url=obj.get("source_url", "") or source_url,
                        status="available",
                    )
                )
        return items or _fallback_parse_products(store_name, query, page_text, source_url)
    except Exception:
        return _fallback_parse_products(store_name, query, page_text, source_url)

def resolve_location(location_str: Any) -> str:
    if isinstance(location_str, dict):
        return pincode_for(location_str)

    loc_clean = str(location_str or "").strip().lower()
    if re.match(r'^\d{6}$', loc_clean):
        return loc_clean
    city_map = {
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
        "noida": "201301"
    }
    for city, pin in city_map.items():
        if city in loc_clean:
            return pin
    return "560001"
