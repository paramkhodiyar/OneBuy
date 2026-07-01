import sys
from playwright.sync_api import sync_playwright

def inspect_zepto_flow():
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
        
        inputs = page.query_selector_all("input")
        for idx, inp in enumerate(inputs):
            print(f"Modal Input #{idx} placeholder: {inp.get_attribute('placeholder')}")
            
        browser.close()

if __name__ == "__main__":
    inspect_zepto_flow()
