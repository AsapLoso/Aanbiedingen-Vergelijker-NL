from playwright.sync_api import sync_playwright
import time

def debug_jumbo_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://www.jumbo.com/aanbiedingen/nu"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        try:
            page.click('#onetrust-accept-btn-handler', timeout=5000)
        except: pass
            
        print("Scrolling...")
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(1)
            
        # Find all links
        links = page.query_selector_all('a')
        print(f"Found {len(links)} links total.")
        
        deal_links = []
        for link in links:
            href = link.get_attribute('href')
            if href and ('/aanbiedingen/' in href or '/producten/' in href):
                deal_links.append(href)
                
        print(f"Found {len(deal_links)} potential deal links.")
        for l in deal_links[:10]:
            print(l)
            
        browser.close()

if __name__ == "__main__":
    debug_jumbo_links()
