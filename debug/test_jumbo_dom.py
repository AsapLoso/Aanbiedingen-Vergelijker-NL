from bs4 import BeautifulSoup
import re

filepath = 'C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/raw/jumbo_2026-04-07/3015512.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

cards = soup.select('[data-testid="product-card"]')
print(f"product-card count: {len(cards)}")
cards2 = soup.select('article.product-container')
print(f"product-container count: {len(cards2)}")

# Let's see what h3 tags or product titles exist
print("\nTitles found:")
for t in soup.select('h1')[:3]:
    print("H1 -", t.text.strip())

# See if it's a grid page or a single page
grid = soup.select('.jum-grid')
print(f"Grid containers: {len(grid)}")

