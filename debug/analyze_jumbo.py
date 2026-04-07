from bs4 import BeautifulSoup
import json

with open(r'c:\Users\Deuts\OneDrive - Delft University of Technology\Misc\Gemini\Boodschappen\data\raw\jumbo_listing_current_2026-04-07.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'lxml')

cards = soup.select('[data-testid="product-card"], article.product-container, [data-testid="promotions-card"], a[href*="/aanbiedingen/"]')
print(f"Cards found: {len(cards)}")

deals = []
for card in cards[:5]:
    text = card.get_text(" ", strip=True)
    href = card.get('href') or (card.find('a').get('href') if card.find('a') else None)
    deals.append({'text': text[:100], 'href': href})

print(json.dumps(deals, indent=2))
