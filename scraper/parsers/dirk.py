"""
dirk.py — Dirk deals parser.

Parses Dirk HTML snapshots using a hybrid approach:
1. JSON-LD (schema.org) for accurate prices (~50% of items)
2. DOM parsing for the rest (handles cents-only prices like €0.89)
3. Date extraction from "tot en met" period labels

Insights from Dirk's HTML (April 2026):
- Product cards: <article data-product-id="...">
- Name:          a.bottom > p.title
- Unit/size:     a.bottom > span.subtitle  (e.g. "500 g", "Per stuk")
- Price (normal): span.hasEuros = euros, span.price-small = cents
- Price (cheap):  span.price-large = cents only (no hasEuros, no price-small)
- Original price: span.regular-price contains "van X.XX"
- JSON-LD:       <script type="application/ld+json"> with @type=ItemList
- Date:          span.date inside "tot en met" parent text
"""

import re
from .base import BaseParser


class DirkParser(BaseParser):

    STORE = "Dirk"
    BASE_URL = "https://www.dirk.nl"

    def parse(self, soup):
        """Parse Dirk deals from a BeautifulSoup object."""
        print("🔍 Parsing Dirk...")

        date_end = self._extract_dates(soup)

        # JSON-LD: accurate prices for the subset it covers
        jsonld_data = self.extract_jsonld(soup)
        jsonld_products = []
        jsonld_skus = set()
        if jsonld_data:
            jsonld_products = self._parse_jsonld(soup, jsonld_data, date_end)
            jsonld_skus = {str(p.get("_sku", "")) for p in jsonld_products}

        # DOM: fill in the rest
        dom_products = self._parse_dom(soup, date_end, skip_skus=jsonld_skus)

        # Merge & clean
        all_products = jsonld_products + dom_products
        for p in all_products:
            p.pop("_sku", None)

        print(f"   Found {len(all_products)} deals "
              f"({len(jsonld_products)} JSON-LD + {len(dom_products)} DOM).")
        return all_products

    # ── Date extraction ──────────────────────────────────────────────

    def _extract_dates(self, soup):
        """Extract 'tot en met' date from Dirk's date labels."""
        for el in soup.select("span.date"):
            parent_text = el.parent.get_text(" ", strip=True) if el.parent else ""
            if "tot en met" in parent_text.lower():
                date_str = el.get_text(strip=True)
                return self.parse_date(date_str)
        return None

    # ── JSON-LD parsing ──────────────────────────────────────────────

    def _parse_jsonld(self, soup, jsonld, date_end):
        """Parse using JSON-LD prices, enriched with DOM data."""
        products = []

        # Build SKU -> article card lookup
        card_lookup = {}
        for card in soup.find_all("article"):
            pid = card.get("data-product-id")
            if pid:
                card_lookup[pid] = card

        # Navigate JSON-LD ItemList
        items = []
        if isinstance(jsonld, dict) and "@graph" in jsonld:
            for node in jsonld["@graph"]:
                if node.get("@type") == "ItemList":
                    items = node.get("itemListElement", [])
                    break
        elif isinstance(jsonld, dict) and jsonld.get("@type") == "ItemList":
            items = jsonld.get("itemListElement", [])

        for entry in items:
            try:
                item = entry.get("item", {})
                name = item.get("name", "")
                sku = str(item.get("sku", ""))
                price = float(item.get("offers", {}).get("price", 0))

                images = item.get("image", [])
                image_url = images[0] if isinstance(images, list) and images else images if isinstance(images, str) else None

                # Enrich from DOM
                unit_size, original_price, deal_tag = None, None, None
                card = card_lookup.get(sku)
                if card:
                    unit_size = self._dom_unit(card)
                    original_price = self._dom_original_price(card)
                    deal_tag = self._dom_deal_tag(card)

                deal = self.make_deal(
                    store=self.STORE, name=name, price=price,
                    original_price=original_price,
                    tag=deal_tag, image=image_url, unit=unit_size,
                    raw_price=str(price), date_end=date_end,
                    raw_html=str(card) if card else None
                )
                deal["_sku"] = sku
                products.append(deal)
            except Exception:
                pass

        return products

    # ── DOM parsing ──────────────────────────────────────────────────

    def _parse_dom(self, soup, date_end, skip_skus=None):
        """Parse from DOM cards. Handles cents-only prices."""
        skip_skus = skip_skus or set()
        products = []

        for card in soup.find_all("article"):
            try:
                pid = card.get("data-product-id", "")
                if pid and pid in skip_skus:
                    continue

                name_el = card.select_one("a.bottom p.title")
                name = name_el.get_text(strip=True) if name_el else None
                if not name:
                    continue

                # Price
                deal_price, raw_price = self._dom_price(card)
                original_price = self._dom_original_price(card)
                deal_tag = self._dom_deal_tag(card)

                img_el = card.select_one("img.main-image") or card.find("img")
                image_url = self.clean_image_url(img_el, self.BASE_URL)

                unit_size = self._dom_unit(card)

                products.append(self.make_deal(
                    store=self.STORE, name=name, price=deal_price,
                    original_price=original_price,
                    tag=deal_tag, image=image_url, unit=unit_size,
                    raw_price=raw_price, date_end=date_end,
                    raw_html=str(card)
                ))
            except Exception:
                pass

        return products

    # ── DOM helpers ──────────────────────────────────────────────────

    @staticmethod
    def _dom_price(card):
        """Extract price from a Dirk article card. Returns (price, raw_text)."""
        euros_el = card.select_one("span.hasEuros")
        cents_el = card.select_one("span.price-small")
        large_el = card.select_one("span.price-large")

        if euros_el and cents_el:
            raw = f"{euros_el.get_text(strip=True)}.{cents_el.get_text(strip=True)}"
            return float(raw), raw
        elif large_el and not cents_el:
            cents_val = large_el.get_text(strip=True)
            raw = f"0.{cents_val}"
            return float(raw), raw
        return 0.0, ""

    @staticmethod
    def _dom_original_price(card):
        """Extract 'van X.XX' original price."""
        orig_el = card.select_one("span.regular-price")
        if orig_el:
            m = re.search(r'(\d+[.,]\d+)', orig_el.get_text(strip=True))
            if m:
                return float(m.group(1).replace(",", "."))
        return None

    @staticmethod
    def _dom_deal_tag(card):
        """Extract deal tag label, filtering out price labels."""
        label_el = card.select_one(".label span")
        if label_el:
            lt = label_el.get_text(strip=True)
            if lt and "van" not in lt.lower():
                return lt
        return None

    @staticmethod
    def _dom_unit(card):
        """Extract unit/size from subtitle."""
        unit_el = card.select_one("a.bottom span.subtitle")
        return unit_el.get_text(strip=True) if unit_el else None
