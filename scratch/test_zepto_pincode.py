import sys
from playwright.sync_api import sync_playwright

def inspect_zepto_pincode():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.zepto.com/")
        page.wait_for_timeout(3000)
        
        print("Clicking Select Location...")
        page.click("text=Select Location")
        page.wait_for_timeout(2000)
        
        print("Typing pincode 700001 on Zepto...")
        page.fill('input[placeholder="Search a new address"]', '700001')
        page.wait_for_timeout(3000)
        
        divs = page.query_selector_all("div")
        count = 0
        for d in divs:
            txt = d.inner_text().strip().replace("\n", " | ")
            if txt and count < 25 and ("Kolkata" in txt or "700001" in txt or "West Bengal" in txt or "B.B.D" in txt):
                print(f"Div #{count} (tag: {d.evaluate('el => el.tagName')}, class: {d.get_attribute('class')}): {txt[:120]}")
                count += 1
                
        browser.close()

if __name__ == "__main__":
    inspect_zepto_pincode()
