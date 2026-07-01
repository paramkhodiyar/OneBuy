from typing import Any, List, Optional
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from .base import CommerceTool, CommerceItem
from .gemini_parser import resolve_location, parse_products_with_gemini
from .location import city_for


def _brand_from_name(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2 and parts[0].lower() == "the":
        return " ".join(parts[:3])
    return " ".join(parts[:2]) if len(parts) >= 2 else name


def _parse_instamart_text(query: str, page_text: str, source_url: str) -> List[CommerceItem]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    query_words = [word for word in query.lower().split() if len(word) > 2]
    items: List[CommerceItem] = []
    seen = set()

    for index, line in enumerate(lines):
        if not line.upper().endswith("MINS"):
            continue

        window = lines[index + 1:index + 9]
        name = ""
        pack = ""
        prices: List[float] = []
        for candidate in window:
            lower = candidate.lower()
            if lower in {"ad", "sponsored", "love is adding what matters"} or "off" in lower:
                continue
            if not name and not any(token in lower for token in [" g", " kg", " ml", " combo"]) and not candidate.isdigit():
                name = candidate
                continue
            if name and not pack and any(token in lower for token in [" g", " kg", " ml", " combo"]):
                pack = candidate
                continue
            if candidate.isdigit():
                prices.append(float(candidate))

        if not name or not prices:
            continue
        if query_words and not any(word in name.lower() for word in query_words):
            continue

        final_price = prices[0]
        mrp = prices[-1] if len(prices) > 1 and prices[-1] >= final_price else final_price
        key = (name.lower(), pack.lower(), final_price)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            CommerceItem(
                store="Swiggy Instamart",
                price=mrp,
                delivery_time=line,
                coupons="",
                final_cost=final_price,
                name=name,
                brand=_brand_from_name(name),
                pack_size=pack,
                source_url=source_url,
            )
        )

    return items[:16]


class InstamartTool(CommerceTool):
    def search(self, query: str, location: Optional[Any] = None) -> List[CommerceItem]:
        pincode = resolve_location(location)
        city_base = city_for(location).strip().lower()
        context_options = {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if isinstance(location, dict) and location.get("latitude") and location.get("longitude"):
            context_options["geolocation"] = {
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"]),
            }
            context_options["permissions"] = ["geolocation"]
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(**context_options)
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()
                page.set_default_timeout(7000)
                page.set_default_navigation_timeout(15000)
                page.goto("https://www.swiggy.com/")
                page.wait_for_timeout(3000)
                
                try:
                    page.fill('input[placeholder="Enter your delivery location"]', pincode)
                    page.wait_for_timeout(2500)
                    
                    divs = page.query_selector_all("div")
                    for d in divs:
                        txt = d.inner_text().strip().lower()
                        if (pincode in txt or city_base in txt) and len(txt) < 95:
                            d.click()
                            break
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
                
                page.goto(f"https://www.swiggy.com/instamart/search?custom_back=true&query={quote_plus(query)}")
                page.wait_for_timeout(4000)
                
                body_text = page.query_selector("body").inner_text()
                source_url = page.url
                parsed_items = _parse_instamart_text(query, body_text, source_url)
                if parsed_items:
                    browser.close()
                    return parsed_items
                browser.close()
                return parse_products_with_gemini("Swiggy Instamart", query, body_text, source_url)
        except Exception:
            return []
