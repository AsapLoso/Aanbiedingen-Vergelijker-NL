from .base import Scraper
import os

class AldiScraper(Scraper):
    def __init__(self, base_dir):
        super().__init__("Aldi", base_dir)

    def scrape(self, week, year, force=False):
        # Aldi URL pattern: https://folder.aldi.nl/fixed/{year}/folder-week-{week}-magnolia//GetPDF.ashx
        # Note: 'magnolia' might be a variable part, but let's try the pattern found.
        # Sometimes it's just folder-week-{week}
        
        # Try constructing the URL
        url = f"https://folder.aldi.nl/fixed/{year}/folder-week-{week}-magnolia//GetPDF.ashx"
        
        save_dir = self.get_store_dir(week, year)
        filename = f"aldi_week_{week}_{year}.pdf"
        filepath = os.path.join(save_dir, filename)
        
        if os.path.exists(filepath) and not force:
            print(f"Aldi flyer for week {week} already exists.")
            return filepath

        print(f"Attempting to download Aldi flyer from {url}")
        result = self.download_file(url, filepath)
        
        if not result:
            # Fallback: try without 'magnolia' if that was specific to week 48
            # Or maybe it's just 'folder-week-{week}'
            # For now, let's stick to the one we saw, but maybe we need to be more dynamic later.
            pass
            
        return result
