import re
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


def _query_variants(query: str) -> List[str]:
    cleaned = re.sub(r"\s+", " ", query).strip()
    variants = []
    if cleaned:
        variants.append(cleaned)

    without_quantity = re.sub(
        r"\b\d+(?:\.\d+)?\s*(?:ml|l|litre|liter|g|gm|kg|pcs?|pieces?)\b",
        " ",
        cleaned,
        flags=re.I,
    )
    without_quantity = re.sub(r"\s+", " ", without_quantity).strip()
    if without_quantity and without_quantity.lower() != cleaned.lower():
        variants.append(without_quantity)

    return list(dict.fromkeys(variants))


def _extract_cards(page: Any, query: str) -> List[dict]:
    return page.evaluate(
        """(query) => {
            const queryWords = query.toLowerCase().split(/\\s+/).filter((w) => w.length > 2);
            return Array.from(document.querySelectorAll('a[href*="/pn/"]')).map((a) => {
                const lines = (a.innerText || '').split('\\n').map((line) => line.trim()).filter(Boolean);
                const prices = lines
                    .map((line) => line.match(/^₹\\s*([0-9]+(?:\\.[0-9]+)?)/))
                    .filter(Boolean)
                    .map((match) => Number(match[1]));
                const name = lines.find((line) =>
                    !line.startsWith('₹') &&
                    line.toLowerCase() !== 'add' &&
                    !/^\\d+(?:\\.\\d+)?$/.test(line) &&
                    !/^\\([^)]+\\)$/.test(line) &&
                    !line.toLowerCase().includes('off') &&
                    !line.toLowerCase().includes('bestseller') &&
                    !/^\\d+\\s*(?:pack|pc|pcs|g|kg|ml|l)/i.test(line)
                ) || '';
                const pack = lines.find((line) => /^\\d+\\s*(?:pack|pc|pcs|g|kg|ml|l)/i.test(line)) || '';
                const matchesQuery = !queryWords.length || queryWords.some((word) => name.toLowerCase().includes(word));
                return {name, pack, prices, href: a.href, matchesQuery};
            }).filter((item) => item.name && item.prices.length && item.matchesQuery);
        }""",
        query,
    )


class ZeptoTool(CommerceTool):
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
                page.goto("https://www.zepto.com/")
                page.wait_for_timeout(3000)
                
                try:
                    page.click("text=Select Location")
                    page.wait_for_timeout(2000)
                    page.fill('input[placeholder="Search a new address"]', pincode)
                    page.wait_for_timeout(3000)
                    
                    divs = page.query_selector_all("div")
                    for d in divs:
                        txt = d.inner_text().strip().lower()
                        if (pincode in txt or city_base in txt) and len(txt) < 95:
                            d.click()
                            break
                    page.wait_for_timeout(3000)
                except Exception:
                    pass
                
                cards = []
                body_text = ""
                source_url = ""
                for search_query in _query_variants(query):
                    page.goto(f"https://www.zepto.com/search?query={quote_plus(search_query)}")
                    page.wait_for_timeout(3500)
                    body_text = page.query_selector("body").inner_text()
                    source_url = page.url
                    if "coming soon" in body_text.lower():
                        browser.close()
                        return [
                            CommerceItem(
                                store="Zepto",
                                price=-1,
                                delivery_time="-",
                                coupons="",
                                final_cost=-1,
                                status="unavailable",
                                note="Zepto reports that delivery is not yet available for the selected location.",
                            )
                        ]
                    cards = _extract_cards(page, query)
                    if cards:
                        break

                if cards:
                    items = []
                    seen = set()
                    for card in cards[:16]:
                        final_price = float(card["prices"][0])
                        mrp = float(card["prices"][-1]) if len(card["prices"]) > 1 and card["prices"][-1] >= final_price else final_price
                        key = (card["name"], card.get("pack", ""), final_price)
                        if key in seen:
                            continue
                        seen.add(key)
                        items.append(
                            CommerceItem(
                                store="Zepto",
                                price=mrp,
                                delivery_time="Quick delivery",
                                coupons="",
                                final_cost=final_price,
                                name=card["name"],
                                brand=_brand_from_name(card["name"]),
                                pack_size=card.get("pack", ""),
                                source_url=card.get("href", page.url),
                            )
                        )
                    browser.close()
                    return items
                
                browser.close()
                return parse_products_with_gemini("Zepto", query, body_text, source_url)
        except Exception:
            return []
