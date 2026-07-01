from typing import Any, List, Optional
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from .base import CommerceTool, CommerceItem
from .gemini_parser import resolve_location, parse_products_with_gemini


def _brand_from_name(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2 and parts[0].lower() == "the":
        return " ".join(parts[:3])
    return " ".join(parts[:2]) if len(parts) >= 2 else name


class AmazonTool(CommerceTool):
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
                page.goto("https://www.amazon.in/s?k=milk&i=nowstore")
                page.wait_for_timeout(3000)
                
                try:
                    page.click("#nav-global-location-popover-link")
                    page.wait_for_timeout(2000)
                    page.fill("#GLUXZipUpdateInput", pincode)
                    page.click("#GLUXZipUpdate input")
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
                
                page.goto(f"https://www.amazon.in/s?k={quote_plus(query)}&i=nowstore")
                page.wait_for_timeout(4000)

                cards = page.evaluate(
                    """(query) => {
                        const queryWords = query.toLowerCase().split(/\\s+/).filter((w) => w.length > 2);
                        return Array.from(document.querySelectorAll('[data-component-type="s-search-result"]')).map((card) => {
                            const titleEl = card.querySelector('h2 span');
                            const priceEl = card.querySelector('.a-price .a-offscreen');
                            const linkEl = card.querySelector('h2 a[href]');
                            const title = titleEl ? titleEl.innerText.trim() : '';
                            const priceText = priceEl ? priceEl.innerText.trim() : '';
                            const priceMatch = priceText.match(/₹\\s*([0-9,.]+)/);
                            const href = linkEl ? linkEl.href : window.location.href;
                            const matchesQuery = !queryWords.length || queryWords.some((word) => title.toLowerCase().includes(word));
                            return {
                                title,
                                price: priceMatch ? Number(priceMatch[1].replace(/,/g, '')) : null,
                                href,
                                matchesQuery
                            };
                        }).filter((item) => item.title && item.price && item.matchesQuery);
                    }""",
                    query,
                )
                if cards:
                    items = []
                    seen = set()
                    for card in cards[:16]:
                        key = (card["title"], card["price"])
                        if key in seen:
                            continue
                        seen.add(key)
                        items.append(
                            CommerceItem(
                                store="Amazon Fresh",
                                price=float(card["price"]),
                                delivery_time="As shown on Amazon",
                                coupons="",
                                final_cost=float(card["price"]),
                                name=card["title"],
                                brand=_brand_from_name(card["title"]),
                                pack_size="",
                                source_url=card.get("href", page.url),
                            )
                        )
                    browser.close()
                    return items
                
                body_text = page.query_selector("body").inner_text()
                source_url = page.url
                browser.close()
                return parse_products_with_gemini("Amazon Fresh", query, body_text, source_url)
        except Exception:
            return []
