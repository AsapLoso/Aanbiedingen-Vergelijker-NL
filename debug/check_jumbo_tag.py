import json
from bs4 import BeautifulSoup
from scraper.parsers.jumbo import JumboParser

html = open('C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/raw/jumbo_2026-04-07/3015512.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'lxml')
p = JumboParser()._parse_promotion_page(soup)

valid_deals = [x for x in p if x['deal_tag']]
print(f"Total parsed items: {len(p)}")
print(f"Items with deal tag: {len(valid_deals)}")

if valid_deals:
    for k,v in valid_deals[0].items():
        if k != 'raw_html':
            print(k, v)
else:
    print("Zero items have a deal tag.")
