from typing import Any, List, Optional
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from .base import CommerceTool, CommerceItem
from .gemini_parser import resolve_location, parse_products_with_gemini

class FlipkartTool(CommerceTool):
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
                page.goto(f"https://www.flipkart.com/search?q={quote_plus(query)}&marketplace=GROCERY")
                page.wait_for_timeout(3000)
                
                try:
                    try:
                        page.click("text=Select city")
                    except Exception:
                        try:
                            page.click("text=Verify Delivery Pincode")
                        except Exception:
                            pass
                    page.wait_for_timeout(2000)
                    
                    inputs = page.query_selector_all("input")
                    for inp in inputs:
                        placeholder = inp.get_attribute('placeholder') or ""
                        if "pincode" in placeholder.lower() or not placeholder:
                            try:
                                inp.fill(pincode)
                                page.keyboard.press("Enter")
                                break
                            except Exception:
                                pass
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
                
                body_text = page.query_selector("body").inner_text()
                source_url = page.url
                browser.close()
                return parse_products_with_gemini("Flipkart Minutes", query, body_text, source_url)
        except Exception:
            return []
