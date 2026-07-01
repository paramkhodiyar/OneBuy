import sys
from playwright.sync_api import sync_playwright

def inspect_fk_pincode():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.flipkart.com/search?q=milk&marketplace=GROCERY")
        page.wait_for_timeout(3000)
        
        print("Clicking Select city or Verify Delivery Pincode...")
        try:
            page.click("text=Select city")
        except Exception:
            try:
                page.click("text=Verify Delivery Pincode")
            except Exception:
                pass
                
        page.wait_for_timeout(2000)
        
        inputs = page.query_selector_all("input")
        for idx, inp in enumerate(inputs):
            placeholder = inp.get_attribute('placeholder') or ""
            if "pincode" in placeholder.lower() or not placeholder:
                try:
                    inp.fill("700001")
                    page.keyboard.press("Enter")
                    print("Filled pincode!")
                    break
                except Exception as e:
                    print("Failed to fill input:", idx, e)
            
        page.wait_for_timeout(4000)
        print("URL after pincode:", page.url)
        body_text = page.query_selector("body").inner_text()
        print("Snippet after pincode:")
        print(body_text[:1000])
            
        browser.close()

if __name__ == "__main__":
    inspect_fk_pincode()
