"""
html_parser.py — Deal Parser Dispatcher

Routes HTML snapshots to the correct store-specific parser.
Each store parser lives in scraper/parsers/<store>.py

Usage:
    parser = DealParser()
    deals = parser.parse("data/raw/dirk_2026-04-05.html")
"""

import os
from bs4 import BeautifulSoup
from .parsers.base import BaseParser
from .parsers.dirk import DirkParser
from .parsers.aldi import AldiParser
from .parsers.hoogvliet import HoogvlietParser
from .parsers.ah import AHParser
from .parsers.jumbo import JumboParser

# Registry of store parsers
PARSERS = {
    "dirk": DirkParser(),
    "aldi": AldiParser(),
    "hoogvliet": HoogvlietParser(),
    "ah": AHParser(),
    "jumbo": JumboParser(),
}


class DealParser:
    """
    Routes HTML files to the correct store parser.

    Auto-detects the store from the filename and delegates
    to the appropriate parser in scraper/parsers/.
    """

    BS4_PARSER = "lxml"

    def parse(self, filepath):
        """Parse an HTML file or directory. Returns a list of deal dicts."""
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return []

        # Jumbo multi-page: directory of HTMLs
        if os.path.isdir(filepath):
            # rstrip to handle trailing slashes
            clean_path = filepath.rstrip(os.sep).rstrip('/')
            store_key = self._detect_store(os.path.basename(clean_path))
            if store_key and store_key in PARSERS:
                return PARSERS[store_key].parse_dir(filepath)
            print(f"⚠️ No parser for directory: {filepath}")
            return []

        # Single HTML file
        store_key = self._detect_store(os.path.basename(filepath))
        if not store_key or store_key not in PARSERS:
            print(f"⚠️ No parser for: {os.path.basename(filepath)}")
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, self.BS4_PARSER)
        return PARSERS[store_key].parse(soup)

    @staticmethod
    def _detect_store(filename):
        """Detect which store a file belongs to from its name."""
        name = filename.lower()
        for key in ["dirk", "aldi", "hoogvliet", "jumbo"]:
            if key in name:
                return key
        if "ah" in name or "albert" in name:
            return "ah"
        return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        parser = DealParser()
        deals = parser.parse(sys.argv[1])
        print(f"\n{len(deals)} deals parsed.")
    else:
        print("Usage: python -m scraper.html_parser <path_to_html>")
