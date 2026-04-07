from bs4 import BeautifulSoup

with open(r'c:\Users\Deuts\OneDrive - Delft University of Technology\Misc\Gemini\Boodschappen\data\raw\aldi_next_2026-04-07.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'lxml')

print(f"Title: {soup.title.string if soup.title else 'No Title'}")

# Look for typical product containers or loading indicators
articles = soup.find_all('article')
print(f"Articles found: {len(articles)}")

# Print text of first 10 large headers (h1, h2, h3)
headers = soup.find_all(['h1', 'h2', 'h3'])
print("Headers:")
for h in headers[:10]:
    print(" -", h.get_text().strip())

# Check for loading classes
loaders = soup.find_all(class_=lambda c: c and 'load' in c.lower())
print(f"Elements containing 'load' in class: {len(loaders)}")
