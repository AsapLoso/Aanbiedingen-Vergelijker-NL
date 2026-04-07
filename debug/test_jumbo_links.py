from bs4 import BeautifulSoup
import re

filepath = 'C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/raw/jumbo_listing_current_2026-04-07.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

anchors = soup.find_all('a', href=True)
print(f"Total anchors: {len(anchors)}")

promo_links = set()
for a in anchors:
    href = a['href']
    if '/aanbiedingen/' in href:
        promo_links.add(href)

for link in sorted(list(promo_links))[:20]:
    print(link)

