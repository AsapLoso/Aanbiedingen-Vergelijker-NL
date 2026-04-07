import os
from scraper.html_parser import JumboParser

dirpath = 'C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/raw/jumbo_2026-04-07'
parser = JumboParser()
products = parser.parse_dir(dirpath)
print(f"Products parsed: {len(products)}")
if products:
    print(f"Sample product: {products[0]}")
