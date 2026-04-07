"""Find actual product name/price structure in Aldi."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup

with open("data/raw/aldi_2026-04-05.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

# The card container should have testid like "product-tile-grid-product-tile-1"
# Let's find elements with name, price, unit sub-elements
name_els = soup.select('[data-testid$="-name"]')
print(f"Name elements: {len(name_els)}")
if name_els:
    for el in name_els[:5]:
        tid = el.get("data-testid", "")
        print(f"  {tid}: {el.get_text(strip=True)[:60]}")

price_els = soup.select('[data-testid$="-price"]')
print(f"\nPrice elements: {len(price_els)}")
if price_els:
    for el in price_els[:5]:
        tid = el.get("data-testid", "")
        print(f"  {tid}: {el.get_text(strip=True)[:60]}")

unit_els = soup.select('[data-testid$="-unit"]')
print(f"\nUnit elements: {len(unit_els)}")
if unit_els:
    for el in unit_els[:5]:
        tid = el.get("data-testid", "")
        print(f"  {tid}: {el.get_text(strip=True)[:60]}")

promo_els = soup.select('[data-testid$="-promo"]')
print(f"\nPromo elements: {len(promo_els)}")
if promo_els:
    for el in promo_els[:5]:
        tid = el.get("data-testid", "")
        print(f"  {tid}: {el.get_text(strip=True)[:60]}")

# Find the content section which groups name+price+unit
content_els = soup.select('[data-testid$="-content"]')
print(f"\nContent sections: {len(content_els)}")
if content_els:
    card = content_els[0]
    print(f"\n=== FIRST CONTENT SECTION ===")
    print(card.prettify()[:2000])
