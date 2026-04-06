from .web_scraper import WebScraper
import re

class AHWebScraper(WebScraper):
    def __init__(self):
        super().__init__("Albert Heijn", headless=False)

    def parse_deals(self, page):
        url = "https://www.ah.nl/bonus"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        self.accept_cookies(page)
        
        # User reported that a refresh is often needed to bypass blocks/loading issues
        import time
        print("Waiting 5 seconds before reload (anti-bot workaround)...")
        time.sleep(5)
        print("Reloading page...")
        page.reload()
        print("Waiting 5 seconds after reload...")
        time.sleep(5)
        
        print("Scrolling to load all deals...")
        page.screenshot(path="ah_debug_before_scroll.png")
        self.scroll_to_bottom(page)
        page.screenshot(path="ah_debug_after_scroll.png")
        
        print("Extracting products...")
        products = []
        
        try:
            # Use partial match for the class as it seems to be hashed/dynamic
            # a[class*="promotion-card_root"]
            page.wait_for_selector('a[class*="promotion-card_root"]', timeout=10000)
            cards = page.query_selector_all('a[class*="promotion-card_root"]')
        except:
            print("Could not find product items.")
            cards = []
            
        print(f"Found {len(cards)} potential product cards.")
        
        for card in cards:
            try:
                # Name
                # Usually in a span inside a p, or aria-label
                # aria-label="Klikbaar:AH Prei, 2 voor 0.69, Los, 2 stuks, van 1.1, voor 0.69"
                aria_label = card.get_attribute('aria-label')
                name = "Unknown"
                if aria_label and "Klikbaar:" in aria_label:
                    parts = aria_label.replace("Klikbaar:", "").split(',')
                    if parts:
                        name = parts[0].strip()
                
                if name == "Unknown":
                    # Fallback to text content
                    # The structure is complex, usually the first text block is the name
                    text_content = card.inner_text().split('\n')
                    if text_content:
                        name = text_content[0]

                # Price extraction
                # Price is often scattered in spans. 
                # aria-label contains "voor 0.69"
                deal_price = 0.0
                price_text = None
                
                if aria_label:
                    # Regex for "voor 0.69" or "0.69"
                    match = re.search(r'voor\s*(\d+[.,]\d+)', aria_label)
                    if match:
                        price_text = match.group(1)
                        deal_price = float(price_text.replace(',', '.'))
                    else:
                        # Try finding just a price pattern
                        match = re.search(r'(\d+[.,]\d+)', aria_label)
                        if match:
                             price_text = match.group(1)
                             try:
                                 deal_price = float(price_text.replace(',', '.'))
                             except: pass

                # Image
                img_el = card.query_selector('img')
                image_url = img_el.get_attribute('src') if img_el else None
                
                # Deal Tag
                # Often in the aria label "2 voor 0.69"
                deal_tag = None
                if aria_label:
                     if "1+1 gratis" in aria_label:
                         deal_tag = "1+1 gratis"
                     elif "2e halve prijs" in aria_label:
                         deal_tag = "2e halve prijs"
                     elif "voor" in aria_label:
                         # extract "2 voor 0.69"
                         match = re.search(r'(\d+\s+voor\s+\d+[.,]\d+)', aria_label)
                         if match:
                             deal_tag = match.group(1)

                products.append({
                    'store': self.store_name,
                    'week': self.get_week_number(),
                    'year': self.get_year(),
                    'product_name': name,
                    'price_text': price_text,
                    'deal_price': deal_price,
                    'original_price': None,
                    'unit_size': None,
                    'deal_tag': deal_tag,
                    'image_url': image_url,
                    'category': None
                })
            except Exception as e:
                print(f"Error parsing card: {e}")
                
        return products
