import re
from typing import Any, List, Optional
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from .base import CommerceTool, CommerceItem
from .gemini_parser import resolve_location, parse_products_with_gemini
from .location import city_for

class BlinkitTool(CommerceTool):
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
                page.goto("https://blinkit.com/")
                page.wait_for_timeout(2000)
                
                try:
                    page.fill('input[placeholder="search delivery location"]', pincode)
                    page.wait_for_timeout(2500)
                    
                    clicked = False
                    divs = page.query_selector_all("div")
                    for d in divs:
                        txt = d.inner_text().strip().lower()
                        if (pincode in txt or city_base in txt) and len(txt) < 95:
                            d.click()
                            clicked = True
                            break
                            
                    if not clicked:
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("Enter")
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
                
                page.goto(f"https://blinkit.com/s/?q={quote_plus(query)}")
                page.wait_for_timeout(4000)
                
                body_text = page.query_selector("body").inner_text()
                source_url = page.url
                browser.close()
                return parse_products_with_gemini("Blinkit", query, body_text, source_url)
        except Exception:
            return []
