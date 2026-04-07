"""
aldi.py — Aldi deals parser.

Parses Aldi HTML snapshots using data-testid attributes.
Structure (April 2026):
- Cards are identified by components sharing a common prefix, e.g., 'product-tile-grid-product-tile-1'
- Name:  [data-testid$="-product-name"]
- Price: [data-testid$="-tag-current-price"]
- Unit:  [data-testid$="-tag-sales-unit"]
- Promo: [data-testid$="-tag-promo"]
- Image: [data-testid$="-image"]
"""

import re
from .base import BaseParser


class AldiParser(BaseParser):

    STORE = "Aldi"
    BASE_URL = "https://www.aldi.nl"

    def parse(self, soup):
        """Parse Aldi deals from a BeautifulSoup object."""
        print("🔍 Parsing Aldi...")

        # Extract date/period if possible
        # Aldi usually has "Vanaf maandag ..." or similar headers
        date_start = self._extract_date_context(soup)

        products = []
        
        # We find all "content" or "name" elements to identify the number of products
        # Based on investigation, product-name testids are reliable indicators
        name_els = soup.select('[data-testid$="-product-name"]')
        
        for name_el in name_els:
            try:
                # Extract the common prefix (e.g., "product-tile-grid-product-tile-1")
                testid = name_el.get("data-testid", "")
                prefix = testid.replace("-product-name", "")
                
                name = name_el.get_text(strip=True)
                if not name:
                    continue
                
                # Find associated elements using the prefix
                price_el = soup.select_one(f'[data-testid="{prefix}-tag-current-price"]')
                unit_el = soup.select_one(f'[data-testid="{prefix}-tag-sales-unit"]')
                promo_el = soup.select_one(f'[data-testid="{prefix}-tag-promo"]')
                img_el = soup.select_one(f'[data-testid="{prefix}-image"]')
                
                # Price extraction
                price_text = price_el.get_text(strip=True) if price_el else ""
                deal_price = self.extract_price(price_text)
                
                # Unit and Tag
                unit_size = unit_el.get_text(strip=True) if unit_el else None
                deal_tag = promo_el.get_text(strip=True) if promo_el else None
                
                # Image
                image_url = self.clean_image_url(img_el, self.BASE_URL) if img_el else None
                
                # Card container for raw HTML
                card_el = soup.select_one(f'[data-testid="{prefix}"]') or name_el.parent.parent
                
                products.append(self.make_deal(
                    store=self.STORE,
                    name=name,
                    price=deal_price,
                    tag=deal_tag,
                    image=image_url,
                    unit=unit_size,
                    raw_price=price_text,
                    date_start=date_start,
                    raw_html=str(card_el) if card_el else None
                ))
            except Exception as e:
                # print(f"Error parsing Aldi item: {e}")
                pass

        print(f"   Found {len(products)} deals.")
        return products

    def _extract_date_context(self, soup):
        """Extract start date from Aldi's 'Vanaf ...' headers."""
        import datetime
        today = datetime.date.today().isoformat()
        
        # Look for the first mention of "Vanaf [Day] [Date]"
        # Example: "Vanaf Ma. 06.04." or "Vanaf 06-04"
        text = soup.get_text(" ", strip=True)
        m = re.search(r'vanaf\s+([a-z.]+\s+)?(\d{1,2}[./-]\d{1,2})', text.lower())
        if m:
            date_str = m.group(2)
            parsed = self.parse_date(date_str)
            if parsed:
                return parsed
        
        # Fallback to "today" if no date found
        return today
