import sys
from playwright.sync_api import sync_playwright

def inspect_blinkit_loc_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://blinkit.com/")
        page.wait_for_timeout(3000)
        
        print("Filling location...")
        page.fill('input[placeholder="search delivery location"]', 'Delhi')
        page.wait_for_timeout(2000)
        
        suggestions = page.query_selector_all("div")
        suggestion_texts = []
        for s in suggestions:
            txt = s.inner_text().strip()
            if txt and "Delhi" in txt and len(txt) < 100:
                suggestion_texts.append(txt)
                
        print("Suggestions count:", len(suggestion_texts))
        for idx, txt in enumerate(suggestion_texts[:10]):
            print(f"Suggestion #{idx}: {txt}")
            
        click_target = page.locator("text=Delhi").first
        if click_target:
            click_target.click()
            page.wait_for_timeout(3000)
            print("Location set. Current URL:", page.url)
            
            page.goto("https://blinkit.com/s/?q=milk")
            page.wait_for_timeout(3000)
            print("Search page loaded. URL:", page.url)
            
            products = page.query_selector_all("a")
            print("Blinkit products count:", len(products))
            for idx, p_el in enumerate(products[:15]):
                txt = p_el.inner_text().strip().replace('\n', ' | ')
                if txt and ("milk" in txt.lower() or "₹" in txt):
                    print(f"Blinkit product #{idx}: {txt}")
        else:
            print("Click target not found")
            
        browser.close()

if __name__ == "__main__":
    inspect_blinkit_loc_flow()
