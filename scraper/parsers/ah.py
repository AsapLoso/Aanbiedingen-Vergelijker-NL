"""
ah.py — Albert Heijn (AH) deals parser.

Parses AH Bonus deals from snapshot HTML.
Structure (April 2026):
- Cards: a[class*="promotion-card_root"], article[class*="promotion-card_root"]
- Data: aria-label contains name, price, and deal description.
- Example aria-label: "Klikbaar:AH Verse melk, 2 voor 2.50, ..."
"""

import re
from .base import BaseParser


class AHParser(BaseParser):

    STORE = "Albert Heijn"
    BASE_URL = "https://www.ah.nl"

    def parse(self, soup):
        """Parse AH deals from a BeautifulSoup object."""
        print("🔍 Parsing Albert Heijn...")
        products = []
        
        # AH dates: "period-selection_current" or labels inside "period-toggle"
        date_start, date_end = self._extract_dates(soup)
        
        # AH cards can be 'a' or 'article' with promotion-card_root class
        cards = soup.select('a[class*="promotion-card_root"], article[class*="promotion-card_root"]')

        for card in cards:
            try:
                aria = card.get("aria-label", "")
                if not aria:
                    # Fallback to text inside if aria-label is missing
                    aria = card.get_text(" ", strip=True)

                # Name from aria-label: "Klikbaar:AH Prei, 2 voor 0.69, ..."
                name = "Unknown"
                if "Klikbaar:" in aria:
                    parts = aria.replace("Klikbaar:", "").split(",")
                    if parts:
                        name = parts[0].strip()
                elif "," in aria:
                    # Generic comma-split fallback
                    name = aria.split(",")[0].strip()
                else:
                    name = aria[:50]

                if name == "Unknown" or not name:
                    continue

                # Price from aria-label
                deal_price = 0.0
                raw_price = ""
                # Look for "voor 2.50" or just a number
                # AH often has "2 voor 3.00" or "0.99"
                m = re.search(r'voor\s*(\d+[.,]\d+)', aria)
                if m:
                    raw_price = m.group(1)
                    deal_price = float(raw_price.replace(",", "."))
                else:
                    # Fallback to first decimal found
                    m = re.search(r'(\d+[.,]\d+)', aria)
                    if m:
                        raw_price = m.group(1)
                        deal_price = float(raw_price.replace(",", "."))

                # Deal tag (e.g., "1+1 gratis", "2 voor 5.00")
                deal_tag = None
                if "1+1 gratis" in aria.lower():
                    deal_tag = "1+1 gratis"
                elif "2e halve prijs" in aria.lower():
                    deal_tag = "2e halve prijs"
                elif "gratis" in aria.lower():
                    # Simple "gratis" check
                    m = re.search(r'\d\+\d\s+gratis', aria.lower())
                    if m: deal_tag = m.group(0)
                
                # Check for "X voor Y"
                m = re.search(r'(\d+\s+voor\s+\d+[.,]\d+)', aria.lower())
                if m:
                    deal_tag = m.group(1)

                # Image
                img_el = card.find("img")
                image_url = self.clean_image_url(img_el, self.BASE_URL)

                # Unit (AH unit size is often in the aria-label after the name)
                # Example: "AH Prei per stuk, 2 voor 2.50"
                unit_size = None
                if "," in aria:
                    parts = aria.split(",")
                    if len(parts) > 1 and "voor" not in parts[1]:
                        unit_size = parts[1].strip()

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
        """Extract start and end dates from AH Bonus period header."""
        # Check period toggle button or header
        date_start, date_end = None, None
        
        # Method 1: The period-selection__current span
        period_el = soup.select_one('[class*="period-selection_current"]')
        if not period_el:
            # Method 2: aria-label on the toggle button
            period_el = soup.select_one('button[id="period-toggle-button"]')
            
        if period_el:
            text = period_el.get_text(" ", strip=True) or period_el.get("aria-label", "")
            # Example: "30 maart t/m 6 april"
            m = re.search(r'(\d+\s+[a-z.]+)\s+t/m\s+(\d+\s+[a-z.]+)', text.lower())
            if m:
                date_start = self.parse_date(m.group(1))
                date_end = self.parse_date(m.group(2))
        
        return date_start, date_end
