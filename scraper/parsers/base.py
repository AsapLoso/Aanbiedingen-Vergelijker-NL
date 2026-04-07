"""
base.py — Shared helpers for all store parsers.

Every store parser inherits from BaseParser and gets:
- _extract_price()     — regex price extraction from messy text
- _clean_image_url()   — normalize relative/protocol-less image URLs
- _extract_jsonld()    — extract schema.org JSON-LD from any page
- _make_deal()         — create a standardized deal dict
"""

import re
import json
import datetime


class BaseParser:
    """Base class with shared parsing utilities."""

    BS4_PARSER = "lxml"

    @staticmethod
    def extract_price(text):
        """Extract the best price float from a messy price string."""
        if not text:
            return 0.0
        matches = re.findall(r'(\d+[.,]\d+)', text)
        for m in matches:
            try:
                val = float(m.replace(",", "."))
                if 0.01 < val < 1000:
                    return val
            except ValueError:
                continue
        return 0.0

    @staticmethod
    def clean_image_url(img_el, base_url=""):
        """Extract and clean an image URL from an <img> element."""
        if not img_el:
            return None
        url = img_el.get("src") or img_el.get("data-src") or ""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = base_url + url
        return url if url else None

    @staticmethod
    def extract_jsonld(soup):
        """Extract JSON-LD structured data from the page."""
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                data = json.loads(s.get_text())
                return data
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    @staticmethod
    def parse_date(text):
        """
        Convert a Dutch date string (e.g. '7 april' or 'Ma. 06.04.') to ISO date (YYYY-MM-DD).
        If no year is found, uses current year.
        If 'vandaag' or 'morgen' is found, returns relative date.
        """
        if not text:
            return None
        
        text = text.lower().strip()
        today = datetime.date.today()

        if "vandaag" in text:
            return today.isoformat()
        if "morgen" in text:
            return (today + datetime.timedelta(days=1)).isoformat()

        # Dutch month mapping
        months = {
            "jan": 1, "januari": 1, "jan.": 1,
            "feb": 2, "februari": 2, "feb.": 2,
            "mrt": 3, "maart": 3, "mrt.": 3, "maa.": 3,
            "apr": 4, "april": 4, "apr.": 4,
            "mei": 5,
            "jun": 6, "juni": 6, "jun.": 6,
            "jul": 7, "juli": 7, "jul.": 7,
            "aug": 8, "augustus": 8, "aug.": 8,
            "sep": 9, "september": 9, "sep.": 9,
            "okt": 10, "oktober": 10, "okt.": 10,
            "nov": 11, "november": 11, "nov.": 11,
            "dec": 12, "december": 12, "dec.": 12
        }

        # Handle '06.04.' or '06-04'
        match_ddmm = re.search(r'(\d{1,2})[./-](\d{1,2})', text)
        if match_ddmm:
            d, m = int(match_ddmm.group(1)), int(match_ddmm.group(2))
            try:
                return datetime.date(today.year, m, d).isoformat()
            except ValueError:
                pass

        # Handle '7 april'
        match_d_month = re.search(r'(\d{1,2})\s+([a-z.]+)', text)
        if match_d_month:
            day = int(match_d_month.group(1))
            month_str = match_d_month.group(2)
            if month_str in months:
                try:
                    return datetime.date(today.year, months[month_str], day).isoformat()
                except ValueError:
                    pass

        return None

    @staticmethod
    def make_deal(store, name, price, tag=None, image=None,
                  unit=None, raw_price="", original_price=None,
                  date_start=None, date_end=None, raw_html=None):
        """Standardized deal format, including raw HTML for auditing."""
        return {
            "store": store,
            "product_name": name,
            "price": price,
            "original_price": original_price,
            "deal_tag": tag,
            "unit_size": unit,
            "image_url": image,
            "raw_price_text": raw_price,
            "date_start": date_start,
            "date_end": date_end,
            "raw_html": raw_html
        }
