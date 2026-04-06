from playwright.sync_api import sync_playwright
import time

def debug_jumbo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://www.jumbo.com/aanbiedingen/nu"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        # Cookie acceptance (try multiple selectors)
        try:
            page.click('#onetrust-accept-btn-handler', timeout=5000)
            print("Clicked cookie button")
        except:
            print("No cookie button found or timed out")
            
        print("Scrolling...")
        # Scroll more to trigger loading
        for _ in range(10):
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(1)
            
        try:
            page.wait_for_selector('article', timeout=10000)
            articles = page.query_selector_all('article')
            print(f"Found {len(articles)} articles.")
            
            populated_count = 0
            empty_count = 0
            
            for i, article in enumerate(articles):
                # Try to find title
                title_el = article.query_selector('h3')
                title_text = title_el.inner_text().strip() if title_el else ""
                
                if title_text:
                    populated_count += 1
                    if populated_count <= 3: # Print first 3 populated
                        print(f"\n--- Populated Article {i+1} ---")
                        print(f"Title: {title_text}")
                        print(article.inner_html())
                        print("-------------------")
                else:
                    empty_count += 1
            
            print(f"\nSummary: {populated_count} populated, {empty_count} empty.")
                
        except Exception as e:
            print(f"Error finding articles: {e}")
            
        browser.close()

if __name__ == "__main__":
    debug_jumbo()
