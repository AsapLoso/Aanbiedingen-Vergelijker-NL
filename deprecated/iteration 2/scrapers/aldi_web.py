from .web_scraper import WebScraper
import re

class AldiWebScraper(WebScraper):
    def __init__(self):
        super().__init__("Aldi")

    def parse_deals(self, page):
        url = "https://www.aldi.nl/aanbiedingen.html"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        self.accept_cookies(page)
        
        print("Scrolling to load all deals...")
        self.scroll_to_bottom(page)
        
        print("Extracting products...")
        products = []
        
        # Select product cards
        # The data-testid includes an index, e.g. "product-tile-grid-product1-product-tile"
        # We fetch all elements with the prefix and filter for the correct suffix to avoid sub-elements.
        try:
            page.wait_for_selector('[data-testid*="product-tile-grid-product"]', timeout=10000)
            all_elements = page.query_selector_all('[data-testid*="product-tile-grid-product"]')
            
            cards = []
            for el in all_elements:
                testid = el.get_attribute("data-testid")
                # We want the root card, which typically ends in "-product-tile"
                # e.g. "product-tile-grid-product1-product-tile"
                # We exclude "image", "price-section", etc.
                if testid and testid.endswith("-product-tile"):
                    cards.append(el)
            
            if not cards:
                print("No cards found with specific suffix. Falling back to broader search...")
                cards = page.query_selector_all('article[class*="product-tile"], div[class*="product-tile"]')
                # Filter out small elements or those without children
                cards = [c for c in cards if len(c.query_selector_all('div')) > 0]

        except Exception as e:
            print(f"Error finding cards: {e}")
            cards = []
            
        print(f"Found {len(cards)} potential product cards.")
        
        for card in cards:
            try:
                # Title
                name_el = card.query_selector('[data-testid*="product-tile-title"]')
                if not name_el:
                    name_el = card.query_selector('[class*="title"]')
                if not name_el:
                    name_el = card.query_selector('h2, h3, h4')
                
                name = name_el.inner_text().strip() if name_el else "Unknown"
                
                if name == "Unknown":
                    # Skip unknown products to avoid noise, or log sparingly
                    continue
                
                # Price extraction
                # User pointed to data-testid="product-tile-price"
                # The text inside might be complex, e.g. "1.29" or with strikethrough
                price_text = None
                deal_price = 0.0
                
                price_el = card.query_selector('[data-testid*="product-tile-price"]')
                if not price_el:
                    price_el = card.query_selector('[class*="tag--price"]')
                
                if price_el:
                    # The price might be split in spans (e.g. 1 . 29)
                    # Get all text
                    price_text = price_el.inner_text().strip().replace('\n', ' ')
                
                # Parse price
                if price_text:
                    try:
                        # Find all price-like patterns
                        # Use a regex that requires digits before and after dot/comma, OR just digits if it's a clean number
                        # But be careful with "20 rollen" -> 20.
                        matches = re.findall(r'(\d+[.,]\d+)', price_text)
                        
                        valid_prices = []
                        for m in matches:
                            clean = m.replace(',', '.')
                            try:
                                val = float(clean)
                                if 0.0 < val < 1000: 
                                    valid_prices.append(val)
                            except: continue
                        
                        if valid_prices:
                            deal_price = valid_prices[0]
                            
                    except: pass
                
                # Image
                img_el = card.query_selector('img')
                image_url = img_el.get_attribute('src') if img_el else None
                if image_url and image_url.startswith('//'):
                    image_url = 'https:' + image_url
                
                # Unit info
                unit_el = card.query_selector('[data-testid*="product-tile-unit"], [class*="unit"]')
                unit_size = unit_el.inner_text().strip() if unit_el else None
                
                # Deal tag
                tag_el = card.query_selector('[data-testid*="product-tile-badge"], [class*="badge"], [class*="label"]')
                deal_tag = tag_el.inner_text().strip() if tag_el else None
                
                # Deduplication check
                if not any(p['product_name'] == name for p in products):
                    products.append({
                        'store': self.store_name,
                        'week': self.get_week_number(),
                        'year': self.get_year(),
                        'product_name': name,
                        'price_text': price_text,
                        'deal_price': deal_price,
                        'original_price': None,
                        'unit_size': unit_size,
                        'deal_tag': deal_tag,
                        'image_url': image_url,
                        'category': None
                    })
            except Exception as e:
                print(f"Error parsing card: {e}")
                
        return products
