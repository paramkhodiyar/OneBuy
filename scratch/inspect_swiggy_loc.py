import sys
from playwright.sync_api import sync_playwright

def inspect_swiggy():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.swiggy.com/")
        page.wait_for_timeout(3000)
        print("Swiggy URL:", page.url)
        
        inputs = page.query_selector_all("input")
        for idx, inp in enumerate(inputs):
            print(f"Input #{idx} placeholder: {inp.get_attribute('placeholder')}")
            
        buttons = page.query_selector_all("button")
        for idx, btn in enumerate(buttons):
            print(f"Button #{idx}: {btn.inner_text().strip()}")
            
        browser.close()

if __name__ == "__main__":
    inspect_swiggy()
