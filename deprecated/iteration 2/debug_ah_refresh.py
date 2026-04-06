from playwright.sync_api import sync_playwright
import time

def debug_ah_refresh():
    with sync_playwright() as p:
        # Launch with a head to see what happens, or headless if confident
        # Using headless=False might be better to emulate a real user if there are bot checks
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url = "https://www.ah.nl/bonus"
        print(f"Navigating to {url}")
        
        try:
            page.goto(url, timeout=30000)
        except Exception as e:
            print(f"Initial navigation failed or timed out: {e}")
            
        print("Waiting 5 seconds...")
        time.sleep(5)
        
        print("Checking title...")
        print(f"Title: {page.title()}")
        
        # Check if we are blocked
        if "Access Denied" in page.content() or "Je hebt geen toegang" in page.content():
            print("Detected Access Denied. Attempting refresh...")
            try:
                page.reload()
                print("Reloaded page. Waiting 5 seconds...")
                time.sleep(5)
                print(f"Title after reload: {page.title()}")
            except Exception as e:
                print(f"Error reloading: {e}")
        else:
            print("Did not detect explicit 'Access Denied' text, but checking content anyway.")
            
        # Check for product cards
        # AH usually uses article[data-testid="product-card"] or similar
        try:
            # Try to accept cookies first if present
            try:
                page.click('#onetrust-accept-btn-handler', timeout=3000)
                print("Clicked cookie button")
            except: pass
            
            cards = page.locator('article, [data-testid="product-card"]')
            count = cards.count()
            print(f"Found {count} product cards.")
            
            if count > 0:
                print("--- First Card Text ---")
                print(cards.first.inner_text()[:200])
                print("-----------------------")
        except Exception as e:
            print(f"Error checking content: {e}")
            
        browser.close()

if __name__ == "__main__":
    debug_ah_refresh()
