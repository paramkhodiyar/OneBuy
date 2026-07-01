import sys
from playwright.sync_api import sync_playwright

def inspect_flipkart():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.flipkart.com/grocery-supermart-store")
        page.wait_for_timeout(3000)
        print("URL:", page.url)
        
        inputs = page.query_selector_all("input")
        for idx, inp in enumerate(inputs):
            print(f"Input #{idx} placeholder: {inp.get_attribute('placeholder')}")
            
        divs = page.query_selector_all("div")
        for idx, d in enumerate(divs):
            txt = d.inner_text().strip()
            if "Deliver to" in txt and len(txt) < 80:
                print(f"Deliver div #{idx}: {txt}")
                
        browser.close()

if __name__ == "__main__":
    inspect_flipkart()
