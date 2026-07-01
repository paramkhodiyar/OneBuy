import sys
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        print("=== ZEPTO SEARCH INSPECTION ===")
        page.goto("https://www.zeptonow.com/search?query=milk")
        page.wait_for_timeout(3000)
        
        zepto_elements = page.query_selector_all("a")
        for idx, el in enumerate(zepto_elements[:15]):
            txt = el.inner_text().strip().replace('\n', ' | ')
            if txt:
                print(f"A #{idx}: {txt}")
                
        div_elements = page.query_selector_all("div[data-testid]")
        for idx, el in enumerate(div_elements[:15]):
            txt = el.inner_text().strip().replace('\n', ' | ')
            if txt:
                print(f"DIV[data-testid] #{idx}: {txt}")

        print("=== BLINKIT SEARCH INSPECTION ===")
        page.goto("https://blinkit.com/s/?q=milk")
        page.wait_for_timeout(3000)
        
        blinkit_elements = page.query_selector_all("a")
        for idx, el in enumerate(blinkit_elements[:15]):
            txt = el.inner_text().strip().replace('\n', ' | ')
            if txt:
                print(f"A #{idx}: {txt}")
                
        div_elements_bl = page.query_selector_all("div[class*='Product']")
        for idx, el in enumerate(div_elements_bl[:15]):
            txt = el.inner_text().strip().replace('\n', ' | ')
            if txt:
                print(f"DIV[Product] #{idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    inspect()
