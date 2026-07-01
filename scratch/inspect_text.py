import sys
from playwright.sync_api import sync_playwright

def inspect_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://blinkit.com/")
        page.wait_for_timeout(3000)
        
        page.fill('input[placeholder="search delivery location"]', 'Delhi')
        page.wait_for_timeout(2000)
        
        # Click suggestion
        suggestions = page.query_selector_all("div")
        for s in suggestions:
            txt = s.inner_text().strip()
            if "Delhi Airport" in txt:
                s.click()
                break
                
        page.wait_for_timeout(4000)
        print("After click URL:", page.url)
        
        page.goto("https://blinkit.com/s/?q=milk")
        page.wait_for_timeout(4000)
        
        body_text = page.query_selector("body").inner_text()
        print("Body text snippet (first 1000 chars):")
        print(body_text[:1000])
        
        browser.close()

if __name__ == "__main__":
    inspect_text()
