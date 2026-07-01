import sys
from playwright.sync_api import sync_playwright

def inspect_swiggy_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.swiggy.com/")
        page.wait_for_timeout(3000)
        
        print("Filling location...")
        page.fill('input[placeholder="Enter your delivery location"]', '700001')
        page.wait_for_timeout(2000)
        
        divs = page.query_selector_all("div")
        for d in divs:
            txt = d.inner_text().strip()
            if "700001" in txt and len(txt) < 80:
                print("Clicking suggestion div:", txt)
                d.click()
                break
                
        page.wait_for_timeout(4000)
        print("URL after location set:", page.url)
        
        page.goto("https://www.swiggy.com/instamart/search?custom_back=1&query=milk")
        page.wait_for_timeout(4000)
        print("Instamart Search URL:", page.url)
        
        body_text = page.query_selector("body").inner_text()
        print("Body text snippet (first 1000 chars):")
        print(body_text[:1000])
        
        browser.close()

if __name__ == "__main__":
    inspect_swiggy_flow()
