import os
import sys
from playwright.sync_api import sync_playwright

def run_debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        page.goto("https://www.zepto.com/")
        page.wait_for_timeout(3000)
        
        try:
            page.click("text=Select Location")
            page.wait_for_timeout(2000)
            page.fill('input[placeholder="Search a new address"]', "700001")
            page.wait_for_timeout(3000)
            
            divs = page.query_selector_all("div")
            for d in divs:
                txt = d.inner_text().strip().lower()
                if ("700001" in txt or "kolkata" in txt) and len(txt) < 95:
                    d.click()
                    break
            page.wait_for_timeout(4000)
        except Exception as e:
            print("Location select error:", e)
            
        print("Navigating to search page...")
        page.goto("https://www.zepto.com/search?query=bread")
        page.wait_for_timeout(6000)
        
        print("Taking screenshot...")
        os.makedirs("/Users/paramkhodiyar/.gemini/antigravity-ide/brain/4a743b8e-153d-4a50-9d33-0ca7c1148d49", exist_ok=True)
        page.screenshot(path="/Users/paramkhodiyar/.gemini/antigravity-ide/brain/4a743b8e-153d-4a50-9d33-0ca7c1148d49/zepto_search.png")
        print("Screenshot saved.")
        
        body_text = page.query_selector("body").inner_text()
        print("Zepto body text length:", len(body_text))
        print("First 500 chars of body text:")
        print(body_text[:500])
        
        browser.close()

if __name__ == "__main__":
    run_debug()
