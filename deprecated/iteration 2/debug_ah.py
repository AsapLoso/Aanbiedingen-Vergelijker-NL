from playwright.sync_api import sync_playwright

def debug_ah():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.ah.nl/bonus")
        
        print("Page title:", page.title())
        
        # Check for access denied
        if "Access Denied" in page.content():
            print("ACCESS DENIED DETECTED")
            
        # Accept cookies
        try:
            page.click('#onetrust-accept-btn-handler', timeout=2000)
            print("Clicked cookie button")
            page.wait_for_timeout(2000)
        except:
            print("No cookie button found")

        # Scroll down
        print("Scrolling...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        
        page.screenshot(path="debug_ah.png")
        print("Saved debug_ah.png")
        
        # Print all links
        links = page.query_selector_all('a')
        print(f"Found {len(links)} links.")
        for i, link in enumerate(links):
            href = link.get_attribute('href')
            if href and ('bonus/groep' in href or 'producten/product' in href):
                print(f"Found deal link: {href}")
                
        # Check for specific classes
        cards = page.query_selector_all('article')
        print(f"Found {len(cards)} articles.")
        
        browser.close()

if __name__ == "__main__":
    debug_ah()
