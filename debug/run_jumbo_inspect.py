import json
from scraper.html_parser import JumboParser

parser = JumboParser()
p = parser._parse_promotion_page('C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/raw/jumbo_2026-04-07/3015512.html')

if not p:
    print("NO PRODUCTS RETURNED!")
else:
    print(f"Products returned: {len(p)}")
    for k, v in p[0].items():
        print(f"{k}: {v}")
