from playwright.sync_api import sync_playwright
import time

def debug_hoogvliet():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Try a simpler URL first
        url = "https://www.hoogvliet.com/aanbiedingen"
        print(f"Navigating to {url}")
        try:
            page.goto(url, timeout=60000)
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return

        # Cookie acceptance
        try:
            page.click('button:has-text("Accepteren"), #onetrust-accept-btn-handler', timeout=5000)
            print("Clicked cookie button")
        except:
            print("No cookie button found or timed out")
            
        print("Scrolling...")
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(1)
            
        # Inspect structure
        # Check for common product card classes
        selectors = ['.product-item', '.ish-productList-item', 'article', '.product-tile']
        
        found = False
        for sel in selectors:
            count = page.locator(sel).count()
            print(f"Selector '{sel}': found {count} elements")
            if count > 0:
                found = True
                first_card = page.locator(sel).first
                print(f"--- First '{sel}' Text ---")
                print(first_card.inner_text())
                
                # Check image alt
                img = first_card.locator('img').first
                if img.count() > 0:
                    print(f"--- Image Alt ---")
                    print(img.get_attribute('alt'))
                    print(f"--- Image Title ---")
                    print(img.get_attribute('title'))
                
                # Find name element
                try:
                    name_el = first_card.get_by_text("Heks'nkaas")
                    if name_el.count() > 0:
                        print(f"--- Name Element HTML ---")
                        print(name_el.first.evaluate("el => el.outerHTML"))
                    else:
                        print("Name element not found by text.")
                except: pass
                
                print("--------------------------")
                break
                
        if not found:
            print("No product cards found with common selectors.")
            print("Page title:", page.title())
            
        browser.close()

if __name__ == "__main__":
    debug_hoogvliet()
