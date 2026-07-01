import sys
from playwright.sync_api import sync_playwright

def inspect_flipkart_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.flipkart.com/search?q=milk&marketplace=GROCERY")
        page.wait_for_timeout(3000)
        print("URL:", page.url)
        
        body_text = page.query_selector("body").inner_text()
        print("Body text snippet (first 1000 chars):")
        print(body_text[:1000])
        
        browser.close()

if __name__ == "__main__":
    inspect_flipkart_search()
