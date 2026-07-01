from typing import Any, List, Optional
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

from .base import CommerceItem, CommerceTool
from .gemini_parser import parse_products_with_gemini, resolve_location


class BigBasketTool(CommerceTool):
    def search(self, query: str, location: Optional[Any] = None) -> List[CommerceItem]:
        pincode = resolve_location(location)
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
                page.goto("https://www.bigbasket.com/")
                page.wait_for_timeout(3000)

                try:
                    page.click("text=Select Location", timeout=2500)
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

                try:
                    inputs = page.query_selector_all("input")
                    for inp in inputs:
                        placeholder = (inp.get_attribute("placeholder") or "").lower()
                        if "location" in placeholder or "pincode" in placeholder or "area" in placeholder:
                            inp.fill(pincode)
                            page.wait_for_timeout(2000)
                            page.keyboard.press("ArrowDown")
                            page.keyboard.press("Enter")
                            break
                    page.wait_for_timeout(2500)
                except Exception:
                    pass

                page.goto(f"https://www.bigbasket.com/ps/?q={quote_plus(query)}")
                page.wait_for_timeout(4000)

                body_text = page.query_selector("body").inner_text()
                source_url = page.url
                browser.close()
                return parse_products_with_gemini("BigBasket Now", query, body_text, source_url)
        except Exception:
            return []
