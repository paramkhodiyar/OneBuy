import sys
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = context.new_page()
            
            print("--- Loading Zepto search for milk ---")
            page.goto("https://www.zeptonow.com/search?query=milk")
            page.wait_for_timeout(3000)
            print("Zepto HTML length:", len(page.content()))
            
            print("--- Loading Blinkit search for milk ---")
            page.goto("https://blinkit.com/s/?q=milk")
            page.wait_for_timeout(3000)
            print("Blinkit HTML length:", len(page.content()))
            
            browser.close()
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    run()
