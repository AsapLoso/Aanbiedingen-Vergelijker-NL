"""Investigate Hoogvliet HTML structure."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup

# Path to the Hoogvliet snapshot
filename = "data/raw/hoogvliet_2026-04-05.html"
if not os.path.exists(filename):
    print(f"File not found: {filename}")
    sys.exit(1)

with open(filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

# 1. Product Cards
print("=== PRODUCT CARDS ===")
els = soup.select(".product-tile")
print(f"Elements with class '.product-tile': {len(els)}")
if els:
    card = els[0]
    print(f"\nExample card HTML (first 1000 chars):")
    print(card.prettify()[:1000])

# 2. Name, Price, Unit, Image inside .product-tile
if els:
    for i, el in enumerate(els[:3]):
        name = el.select_one("h3")
        price = el.select_one(".price-container")
        image = el.select_one("img")
        unit = el.select_one(".product-amount") # Guess based on common patterns
        tag = el.select_one(".promotion-short-title")
        
        print(f"\nItem {i+1}:")
        print(f"  Name:  {name.get_text(strip=True) if name else 'None'}")
        print(f"  Price: {price.get_text(' ', strip=True) if price else 'None'}")
        print(f"  Tag:   {tag.get_text(strip=True) if tag else 'None'}")
        print(f"  Image: {image.get('src') if image else 'None'}")

# 3. Dates
print("\n=== DATE INFO ===")
text = soup.get_text(" ")
m = re.search(r'geldig\s+van[^.]{5,60}', text, re.IGNORECASE)
if m: print(f"Found 'geldig van': {m.group(0)}")
m = re.search(r't/m[^.]{5,30}', text, re.IGNORECASE)
if m: print(f"Found 't/m': {m.group(0)}")

# 4. JSON-LD check
scripts = soup.find_all("script", type="application/ld+json")
print(f"\nJSON-LD scripts: {len(scripts)}")
for s in scripts[:2]:
    print(f"  Script {scripts.index(s)} snippet: {s.get_text()[:200]}")
