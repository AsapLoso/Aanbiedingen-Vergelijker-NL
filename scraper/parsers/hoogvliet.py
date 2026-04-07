"""
hoogvliet.py — Hoogvliet deals parser.

Structure (April 2026):
- Card: .product-tile
- Name: h3
- Price: .price-container
  - Euros: .price-euros span:first-child
  - Cents: .price-cents sup
- Tag: .promotion-short-title (e.g., "1+1 gratis", "2 voor 5.00")
- Image: .product-image-container img (data-image-src or src)
"""

import re
from .base import BaseParser


class HoogvlietParser(BaseParser):

    STORE = "Hoogvliet"
    BASE_URL = "https://www.hoogvliet.com"

    def parse(self, soup):
        """Parse Hoogvliet deals from a BeautifulSoup object."""
        print("🔍 Parsing Hoogvliet...")
        
        # Extract dates from header or filter sidebar
        date_start, date_end = self._extract_dates(soup)

        products = []
        cards = soup.select(".product-tile")

        for card in cards:
            try:
                # Name
                name_el = card.select_one("h3")
                name = name_el.get_text(strip=True) if name_el else None
                if not name:
                    continue

                # Price: euros + cents split across elements
                # Usually we want the 'current' price. 
                # If there are multiple prices (range), we try to find the one after the strike-through or the last one.
                
                deal_price = 0.0
                raw_price = ""
                
                # Hoogvliet often has a hidden structure or specific classes for current vs old price
                # We'll look for .price-container and try to get the 'new' price.
                
                # Check for specific price container which usually holds the active price
                # Based on investigation: '4.09 3 . 49'
                # Let's try to find elements with specific classes first
                
                price_box = card.select_one(".product-price") or card.select_one(".price-container")
                if price_box:
                    # In some cases, there are multiple .price-euros. 
                    # We take the *last* one if there's a discount, as it's typically the valid one.
                    euro_els = price_box.select(".price-euros span:first-child")
                    cent_els = price_box.select(".price-cents sup")
                    
                    if euro_els and cent_els:
                        # Use the last pair found
                        euros = euro_els[-1].get_text(strip=True)
                        cents = cent_els[-1].get_text(strip=True)
                        raw_price = f"{euros}.{cents}"
                        try:
                            deal_price = float(raw_price)
                        except ValueError:
                            pass
                
                # Fallback to text extraction if elements aren't clear
                if deal_price == 0.0:
                    text = price_box.get_text(" ", strip=True) if price_box else ""
                    # If text is "4.09 3.49", we want 3.49
                    matches = re.findall(r'(\d+)\s*[.,]\s*(\d{2})', text)
                    if matches:
                        # Take the last match as the deal price
                        euros, cents = matches[-1]
                        deal_price = float(f"{euros}.{cents}")
                        raw_price = text

                # Deal tag
                tag_el = card.select_one(".promotion-short-title")
                deal_tag = tag_el.get_text(strip=True) if tag_el else None

                # Image
                img_el = card.select_one(".product-image-container img")
                if img_el:
                    image_url = img_el.get("data-image-src") or img_el.get("src")
                    image_url = self.clean_image_url(image_url, self.BASE_URL) if isinstance(image_url, str) else None
                else:
                    image_url = None

                # Unit: Often inside the tag or name at Hoogvliet
                # Hoogvliet doesn't always have a dedicated unit element on the tile
                unit_size = None

                products.append(self.make_deal(
                    store=self.STORE,
                    name=name,
                    price=deal_price,
                    tag=deal_tag,
                    image=image_url,
                    unit=unit_size,
                    raw_price=raw_price,
                    date_start=date_start,
                    date_end=date_end,
                    raw_html=str(card)
                ))
            except Exception:
                pass

        print(f"   Found {len(products)} deals.")
        return products

    def _extract_dates(self, soup):
        """Extract start and end dates from Hoogvliet filter labels or header."""
        date_start, date_end = None, None
        
        # Look for active date labels "Aanbiedingen | 01 april - 07 april"
        # Often in checkboxes or header spans
        date_labels = soup.select('label.filter-checkbox-label, .promotion-header h1')
        for label in date_labels:
            text = label.get_text(" ", strip=True).lower()
            if "|" in text and "-" in text:
                # Extract part after | 
                period_part = text.split("|")[-1].strip()
                # Split by -
                dates = period_part.split("-")
                if len(dates) == 2:
                    date_start = self.parse_date(dates[0])
                    date_end = self.parse_date(dates[1])
                    if date_start and date_end:
                        return date_start, date_end

        return None, None

    def clean_image_url(self, url, base_url=""):
        """Override to handle direct URL strings too."""
        if not url:
            return None
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = base_url + url
        return url
