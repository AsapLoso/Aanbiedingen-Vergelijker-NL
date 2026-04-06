# Iteration 2 Scrapers Package
# Includes both legacy (PDF) and then-new (Web) scrapers.

from .aldi import AldiScraper
from .dirk import DirkScraper
from .publitas import PublitasScraper, get_ah_url, get_jumbo_url, get_hoogvliet_url

from .dirk_web import DirkWebScraper
from .ah_web import AHWebScraper
from .aldi_web import AldiWebScraper
from .jumbo_web import JumboWebScraper
from .hoogvliet_web import HoogvlietWebScraper
