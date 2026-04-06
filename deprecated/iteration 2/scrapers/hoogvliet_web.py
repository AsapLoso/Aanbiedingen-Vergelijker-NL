from .web_scraper import WebScraper
import re

class HoogvlietWebScraper(WebScraper):
    def __init__(self):
        super().__init__("Hoogvliet")

    def parse_deals(self, page):
        url = "https://www.hoogvliet.com/aanbiedingen"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        self.accept_cookies(page)
        
        print("Scrolling to load all deals...")
        # Hoogvliet might need a specific scroll or "load more"
        # For now, standard scroll
        self.scroll_to_bottom(page)
        
        print("Extracting products...")
        products = []
        
        try:
            page.wait_for_selector('.product-tile', timeout=10000)
            cards = page.query_selector_all('.product-tile')
        except:
            print("Could not find product-tile elements.")
            cards = []
            
        print(f"Found {len(cards)} potential product cards.")
        
        for card in cards:
            try:
                # Name
                # Found to be a direct h3
                name_el = card.query_selector('h3')
                name = name_el.inner_text().strip() if name_el else "Unknown"
                
                # Price extraction
                # Structure: .price-euros > span + .price-cents > sup
                price_text = None
                deal_price = 0.0
                
                # Try to find the main price container
                # There might be multiple prices (range), take the first non-strikethrough one
                price_container = card.query_selector('.price-container .non-strikethrough')
                
                if price_container:
                    euros_el = price_container.query_selector('.price-euros span:first-child')
                    cents_el = price_container.query_selector('.price-cents sup')
                    
                    if euros_el and cents_el:
                        euros = euros_el.inner_text().strip()
                        cents = cents_el.inner_text().strip()
                        price_text = f"{euros}.{cents}"
                        try:
                            deal_price = float(price_text)
                        except: pass
                
                # Fallback if structure is different
                if deal_price == 0.0:
                     price_el = card.query_selector('.price-container')
                     if price_el:
                         price_text = price_el.inner_text().strip().replace('\n', ' ')
                         # Regex search with optional spaces
                         match = re.search(r'(\d+)\s*[.,]\s*(\d{2})', price_text)
                         if match:
                             deal_price = float(f"{match.group(1)}.{match.group(2)}")

                # Image
                img_el = card.query_selector('.product-image-container img')
                image_url = img_el.get_attribute('src') if img_el else None
                if image_url and not image_url.startswith('http'):
                    image_url = "https://www.hoogvliet.com" + image_url
                
                # Deal Tag
                tag_el = card.query_selector('.promotion-short-title')
                deal_tag = tag_el.inner_text().strip() if tag_el else None
                
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
