import sys
from playwright.sync_api import sync_playwright

def inspect_amazon():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.amazon.in/s?k=milk&i=nowstore")
        page.wait_for_timeout(3000)
        print("Initial URL:", page.url)
        
        # Look for Deliver to or location picker
        try:
            page.click("#nav-global-location-popover-link")
            print("Clicked location popover link")
            page.wait_for_timeout(2000)
            
            # Fill pincode input
            page.fill("#GLUXZipUpdateInput", "700001")
            page.click("#GLUXZipUpdate input")
            print("Pincode submitted!")
            page.wait_for_timeout(3000)
        except Exception as e:
            print("Failed to set Amazon location:", e)
            
        page.goto("https://www.amazon.in/s?k=milk&i=nowstore")
        page.wait_for_timeout(4000)
        print("Search page URL:", page.url)
        
        body_text = page.query_selector("body").inner_text()
        print("Body snippet:")
        print(body_text[:1000])
        
        browser.close()

if __name__ == "__main__":
    inspect_amazon()
