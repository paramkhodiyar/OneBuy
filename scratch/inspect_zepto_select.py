import sys
from playwright.sync_api import sync_playwright

def inspect_zepto_select():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.goto("https://www.zepto.com/")
        page.wait_for_timeout(3000)
        
        print("Clicking Select Location...")
        page.click("text=Select Location")
        page.wait_for_timeout(2000)
        
        print("Filling Search new address...")
        page.fill('input[placeholder="Search a new address"]', 'Delhi')
        page.wait_for_timeout(3000)
        
        suggestions = page.query_selector_all("h4")
        suggestion_texts = []
        for s in suggestions:
            txt = s.inner_text().strip()
            if txt:
                suggestion_texts.append(txt)
                
        print("Suggestions count (h4):", len(suggestion_texts))
        for idx, txt in enumerate(suggestion_texts):
            print(f"Suggestion #{idx}: {txt}")
            
        divs = page.query_selector_all("div")
        for d in divs:
            txt = d.inner_text().strip()
            if "Delhi" in txt and len(txt) < 80:
                print("Clicking suggestion div:", txt)
                d.click()
                break
                
        page.wait_for_timeout(4000)
        print("URL after location select:", page.url)
        
        page.goto("https://www.zepto.com/search?query=milk")
        page.wait_for_timeout(4000)
        print("Search URL:", page.url)
        
        links = page.query_selector_all("a")
        print("Links count:", len(links))
        for idx, link in enumerate(links[:15]):
            txt = link.inner_text().strip().replace('\n', ' | ')
            if txt and "₹" in txt:
                print(f"Product link #{idx}: {txt}")
                
        browser.close()

if __name__ == "__main__":
    inspect_zepto_select()
