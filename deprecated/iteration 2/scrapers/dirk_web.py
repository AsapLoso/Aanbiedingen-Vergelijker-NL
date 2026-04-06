from .web_scraper import WebScraper
import time
import re

class DirkWebScraper(WebScraper):
    def __init__(self):
        super().__init__("Dirk")

    def parse_deals(self, page):
        url = "https://www.dirk.nl/aanbiedingen"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        self.accept_cookies(page)
        
        # Dirk uses infinite scroll.
        print("Scrolling to load all deals...")
        self.scroll_to_bottom(page)
        
        print("Extracting products...")
        products = []
        
        # Select all product cards
        # Based on inspection, Dirk cards usually have a specific class structure
        # We need to be robust. Let's look for the product card container.
        # Often: .product-card or similar.
        # Let's try to find them by a common attribute or class.
        
        # Wait for at least some products to be visible
        page.wait_for_selector('article', timeout=10000)
        
        cards = page.query_selector_all('article')
        print(f"Found {len(cards)} product cards.")
        
        for card in cards:
            try:
                # Extract details
                # Title is in the bottom part, p tag
                name_el = card.query_selector('a[class*="bottom"] p')
                name = name_el.inner_text().strip() if name_el else "Unknown"
                
                # Price extraction
                # Try specific selectors first
                price_text = None
                deal_price = 0.0
                
                # Try to find the price container
                # Common classes: product-card__price, price, etc.
                price_el = card.query_selector('[class*="price"]')
                if price_el:
                    price_text = price_el.inner_text().strip().replace('\n', '.')
                
                # Fallback: Regex on the whole card text
                if not price_text:
                    card_text = card.inner_text()
                    # Look for price pattern: € 1.99 or 1.99 or 1,99
                    # Dirk often shows big numbers like "1" and small "99"
                    # The text content might be "199" or "1.99"
                    pass
                
                # Parse price
                if price_text:
                    try:
                        # Find all price-like patterns
                        # Matches: 1.99, 1,99, .89, ,89
                        matches = re.findall(r'(\d*[.,]?\d+)', price_text)
                        
                        # Filter matches that look like prices (contain dot or comma, or are just digits if we are desperate)
                        # Better regex: (\d+[.,]\d{2}) or (\.\d{2}) or (,\d{2})
                        # Let's try to find all valid numbers
                        valid_prices = []
                        for m in matches:
                            # Clean up
                            clean = m.replace(',', '.')
                            # Fix .89 -> 0.89
                            if clean.startswith('.'):
                                clean = '0' + clean
                            try:
                                val = float(clean)
                                # Filter out likely non-prices (e.g. year 2025, or very small/large)
                                if 0.1 < val < 1000:
                                    valid_prices.append(val)
                            except:
                                continue
                        
                        if valid_prices:
                            # If "van" is in text, usually the last price is the deal price
                            # "van 1.59 .89" -> [1.59, 0.89] -> 0.89
                            # "ACTIE 1.99" -> [1.99] -> 1.99
                            deal_price = valid_prices[-1]
                            
                            if len(valid_prices) > 1 and "van" in price_text.lower():
                                # Try to set original price too
                                # Assuming the one before the last is original
                                # But sometimes there are 3 numbers?
                                pass
                    except Exception as e:
                        print(f"Error parsing price '{price_text}': {e}")
                
                # If still 0, try to parse from the whole card text as a last resort
                if deal_price == 0.0:
                    try:
                        card_text = card.inner_text()
                        # Look for "1.99" or "1,99"
                        match = re.search(r'(\d+[.,]\d{2})', card_text)
                        if match:
                            clean_price = match.group(1).replace(',', '.')
                            deal_price = float(clean_price)
                            price_text = match.group(1)
                    except:
                        pass

                # Deal tag (e.g. 1+1)
                # Usually a label in the top part
                tag_el = card.query_selector('a[class*="top"] span[class*="label"]') 
                deal_tag = tag_el.inner_text().strip() if tag_el else None
                
                # Image
                img_el = card.query_selector('img')
                image_url = img_el.get_attribute('src') if img_el else None
                
                # Unit/Info
                unit_el = card.query_selector('a[class*="bottom"] span')
                unit_size = unit_el.inner_text().strip() if unit_el else None
                
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
