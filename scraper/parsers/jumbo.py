"""
jumbo.py — Jumbo deals parser.

Handles both:
1. Directory of HTML files (captured individual product pages).
2. Listing page (fallback, but limited data).

Structure (April 2026):
- Product Title: h1 or [data-testid="product-title"]
- Price:         [data-testid="price-container"]
- Image:         img[data-testid="product-image"]
- Deal/Badge:    [data-testid="sale-label"]
"""

import os
from bs4 import BeautifulSoup
from .base import BaseParser


class JumboParser(BaseParser):

    STORE = "Jumbo"
    BASE_URL = "https://www.jumbo.com"

    def parse(self, soup_or_path):
        """Parse Jumbo deals. Routes to parse_dir if passed a path."""
        if isinstance(soup_or_path, str) and os.path.isdir(soup_or_path):
            return self.parse_dir(soup_or_path)
        
        # If it's a single soup object (listing/promotion page)
        return self._parse_promotion_page(soup_or_path)

    def parse_dir(self, dirpath):
        """Parse multiple Jumbo promotion pages from a directory."""
        print(f"🔍 Parsing Jumbo pages from {dirpath}...")
        all_products = []
        html_files = [f for f in os.listdir(dirpath) if f.endswith(".html")]

        for fname in html_files:
            try:
                filepath = os.path.join(dirpath, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    html = f.read()
                soup = BeautifulSoup(html, self.BS4_PARSER)
                
                # Each "product page" for Jumbo is now often a promotion list
                products = self._parse_promotion_page(soup)
                all_products.extend(products)

            except Exception as e:
                print(f"   ⚠️ Error parsing {fname}: {e}")

        print(f"   Found {len(all_products)} deals from {len(html_files)} pages.")
        return all_products

    def _parse_promotion_page(self, soup):
        """Parse a page that might contain a grid of products (Nuxt UI)."""
        products = []
        
        # 1. Extract common dates for all products on this page
        date_start, date_end = self._extract_dates(soup)
        
        # 2. Find all product cards
        # New selector for Nuxt/Jumbo 2026: [data-testid="product-card"] or article.product-container
        cards = soup.select('[data-testid="product-card"]')
        if not cards:
            cards = soup.select('article.product-container')

        for card in cards:
            try:
                # Name
                name_el = card.select_one('h3.title a.title-link') or card.select_one('[data-testid="jum-heading"] a')
                name = name_el.get_text(strip=True) if name_el else None
                if not name:
                    continue

                # Price: Split into whole and fractional parts
                # <span class="whole">2</span><span class="fractional">76</span>
                price_container = card.select_one('.current-price') or card.select_one('[data-testid="product-price"]')
                if price_container:
                    whole = price_container.select_one('.whole')
                    frac = price_container.select_one('.fractional')
                    if whole and frac:
                        raw_price = f"{whole.get_text(strip=True)}.{frac.get_text(strip=True)}"
                    else:
                        raw_price = price_container.get_text(strip=True)
                else:
                    raw_price = ""
                
                deal_price = self.extract_price(raw_price)

                # Image
                img_el = card.select_one('img[data-testid="jum-product-image"]') or card.select_one('img.image')
                image_url = self.clean_image_url(img_el, self.BASE_URL)

                # Deal tag (e.g., "2+1 gratis")
                tag_el = card.select_one('.tag-line') or card.select_one('.jum-tag')
                deal_tag = tag_el.get_text(strip=True) if tag_el else None

                products.append(self.make_deal(
                    store=self.STORE,
                    name=name,
                    price=deal_price,
                    tag=deal_tag,
                    image=image_url,
                    raw_price=raw_price,
                    date_start=date_start,
                    date_end=date_end,
                    raw_html=str(card)
                ))
            except Exception:
                continue
                
        return products

    def _extract_dates(self, soup):
        """Extract start and end dates from the promotion banner."""
        date_start, date_end = None, None
        import re
        
        # New selector: strong[data-testid="promotion-runtime-details"]
        # Example: "Geldig van wo 1 t/m di 7 apr"
        date_el = soup.select_one('[data-testid="promotion-runtime-details"]')
        if not date_el:
            # Fallback to general text
            date_el = soup.select_one('.promotion-runtime') or soup.find(string=re.compile(r'geldig van', re.I))

        if date_el:
            text = date_el.get_text(" ", strip=True).lower()
            # regex to find "wo 1" t/m "di 7 apr"
            # We want to catch "1 t/m 7 apr" or "wo 1 t/m di 7 apr"
            m = re.search(r'van\s+(.*?)\s+t/m\s+(.*)', text)
            if m:
                # parse_date handles "wo 1" by stripping the day name
                date_start = self.parse_date(m.group(1).strip())
                date_end = self.parse_date(m.group(2).strip())
                
        return date_start, date_end
