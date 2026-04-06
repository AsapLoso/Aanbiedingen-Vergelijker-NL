from .web_scraper import WebScraper
import re

class JumboWebScraper(WebScraper):
    def __init__(self):
        super().__init__("Jumbo")

    def parse_deals(self, page):
        url = "https://www.jumbo.com/aanbiedingen/nu"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        self.accept_cookies(page)
        
        print("Scrolling to load all deals...")
        # self.scroll_to_bottom(page) # Default method might be too fast or fail on this page
        import time
        for _ in range(10):
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(1)
        
        print("Collecting product links...")
        # Extract all hrefs that look like product pages
        # Pattern: /producten/name-id
        # Use Python side filtering as it proved more reliable in debug
        anchors = page.query_selector_all('a')
        print(f"DEBUG: Found {len(anchors)} total anchors.")
        
        hrefs = []
        for a in anchors:
            href = a.get_attribute('href')
            if href and ('/producten/' in href or '/aanbiedingen/' in href):
                # Check for ID pattern at the end to distinguish from categories
                # Support both:
                # /producten/name-ID (hyphen separator)
                # /aanbiedingen/name/ID (slash separator)
                if re.search(r'[-/][0-9]+[A-Z0-9]*$', href):
                    hrefs.append(href)
        
        # Deduplicate
        unique_links = list(set(hrefs))
        print(f"Found {len(unique_links)} unique product links.")
        
        products = []
        
        for i, link in enumerate(unique_links):
            full_url = f"https://www.jumbo.com{link}"
            print(f"[{i+1}/{len(unique_links)}] Scraping {full_url}")
            
            try:
                page.goto(full_url, timeout=30000)
                # Wait for price to appear
                try:
                    page.wait_for_selector('[data-testid="price-container"], .current-price, h1', timeout=5000)
                except: pass
                
                # Name
                name_el = page.query_selector('h1')
                if not name_el:
                    name_el = page.query_selector('[data-testid="product-title"]')
                
                name = name_el.inner_text().strip() if name_el else None
                
                if not name:
                    # Try meta title
                    try:
                        name = page.title()
                        if " | Jumbo" in name:
                            name = name.replace(" | Jumbo", "")
                    except: pass
                    
                if not name:
                    name = "Unknown"
                
                # Price
                # Jumbo detail page usually has a clear price container
                price_text = None
                deal_price = 0.0
                
                # Try multiple selectors for price
                price_el = page.query_selector('[data-testid="price-container"]')
                if not price_el:
                    price_el = page.query_selector('.current-price')
                
                if price_el:
                    price_text = price_el.inner_text().strip().replace('\n', '.')
                    
                # Parse price
                if price_text:
                    try:
                        # Matches: 2.39 or 2,39
                        matches = re.findall(r'(\d+[.,]\d+)', price_text)
                        if matches:
                            clean = matches[0].replace(',', '.')
                            deal_price = float(clean)
                    except: pass
                
                # Image
                img_el = page.query_selector('img[data-testid="product-image"]')
                image_url = img_el.get_attribute('src') if img_el else None
                
                # Unit / Deal Tag
                # Look for "2e halve prijs" or similar text
                deal_tag = None
                tag_el = page.query_selector('[data-testid="sale-label"]')
                if tag_el:
                    deal_tag = tag_el.inner_text().strip()
                
                products.append({
                    'store': self.store_name,
                    'week': self.get_week_number(),
                    'year': self.get_year(),
                    'product_name': name,
                    'price_text': price_text,
                    'deal_price': deal_price,
                    'original_price': None,
                    'unit_size': None, # TODO: Extract unit
                    'deal_tag': deal_tag,
                    'image_url': image_url,
                    'category': None
                })
                
            except Exception as e:
                print(f"Error scraping {full_url}: {e}")
                
        return products
