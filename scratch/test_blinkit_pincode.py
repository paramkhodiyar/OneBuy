import sys
from playwright.sync_api import sync_playwright

def inspect_blinkit_pincode():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://blinkit.com/")
        page.wait_for_timeout(3000)
        
        print("Typing pincode 700001 on Blinkit...")
        page.fill('input[placeholder="search delivery location"]', '700001')
        page.wait_for_timeout(3000)
        
        # Print all visible divs containing Kolkata or G.P.O or West Bengal
        divs = page.query_selector_all("div")
        print("Analyzing divs in Blinkit DOM after typing pincode:")
        count = 0
        for d in divs:
            txt = d.inner_text().strip().replace("\n", " | ")
            if txt and count < 20 and ("Kolkata" in txt or "700001" in txt or "West Bengal" in txt or "G.P.O" in txt):
                print(f"Div #{count} (tag: {d.evaluate('el => el.tagName')}, class: {d.get_attribute('class')}): {txt[:120]}")
                count += 1
                
        browser.close()

if __name__ == "__main__":
    inspect_blinkit_pincode()
