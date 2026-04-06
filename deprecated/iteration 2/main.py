import os
import argparse
import datetime
from scrapers.aldi import AldiScraper
from scrapers.dirk import DirkScraper
from scrapers.publitas import PublitasScraper, get_ah_url, get_jumbo_url, get_hoogvliet_url
from database.db import init_db, add_flyer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_scrapers(week=None, year=None, store_selection=None, force=False):
    if not week:
        today = datetime.date.today()
        week = today.isocalendar()[1]
        year = today.year
    
    print(f"Running scrapers for Week {week}, {year} (Force Overwrite: {force})")
    
    all_scrapers = [
        AldiScraper(BASE_DIR),                                          # 1
        DirkScraper(BASE_DIR),                                          # 2
        PublitasScraper("AH", BASE_DIR, get_ah_url),                    # 3
        PublitasScraper("Jumbo", BASE_DIR, get_jumbo_url),              # 4
        PublitasScraper("Hoogvliet", BASE_DIR, get_hoogvliet_url)       # 5
    ]
    
    scrapers_to_run = []
    if not store_selection or '0' in str(store_selection):
        print("Selected: All Stores")
        scrapers_to_run = all_scrapers
    else:
        print(f"Selection string: {store_selection}")
        indices = set(str(store_selection))
        # Map: 1->0, 2->1, etc.
        for char in indices:
            if char.isdigit():
                idx = int(char) - 1
                if 0 <= idx < len(all_scrapers):
                    scrapers_to_run.append(all_scrapers[idx])
        
        # Sort by original index to maintain order if needed, or just run
        scrapers_to_run.sort(key=lambda s: all_scrapers.index(s))
        
    if not scrapers_to_run:
        print("No valid stores selected. Defaulting to ALL.")
        scrapers_to_run = all_scrapers

    for scraper in scrapers_to_run:
        try:
            path = scraper.scrape(week, year, force=force)
            if path:
                flyer_type = 'pdf' if path.endswith('.pdf') else 'images'
                add_flyer(scraper.store_name, week, year, flyer_type, path)
                print(f"Successfully scraped {scraper.store_name}")
            else:
                print(f"Failed to scrape {scraper.store_name}")
        except Exception as e:
            print(f"Error running scraper for {scraper.store_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--scrape', action='store_true', help='Run scrapers')
    parser.add_argument('--week', type=int, help='Week number')
    parser.add_argument('--year', type=int, help='Year')
    parser.add_argument('--server', action='store_true', help='Run web server')
    parser.add_argument('--stores', type=str, help='Stores to scrape (0=All, 1=Aldi, 2=Dirk, 3=AH, 4=Jumbo, 5=Hoogvliet)')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing flyers (Scraping)')
    parser.add_argument('--force-preprocess', action='store_true', help='Force re-process existing pages (Preprocessing)')
    parser.add_argument('--preprocess', action='store_true', help='Preprocess PDFs (split & downsample)')
    parser.add_argument('--extract', action='store_true', help='Extract data using Gemini')
    parser.add_argument('--model', type=str, default="models/gemini-2.5-pro", help='Gemini model name')
    parser.add_argument('--debug', action='store_true', help='Enable visual debugging')
    parser.add_argument('--visualize', action='store_true', help='Visualize existing DB data')
    parser.add_argument('--web', action='store_true', help='Run web scrapers (new method)')
    
    args = parser.parse_args()
    
    init_db()
    
    if args.scrape:
        run_scrapers(args.week, args.year, args.stores, args.force)
        
    if args.preprocess:
        from preprocess import run_preprocessing
        # Determine path
        base_dir = os.path.join(BASE_DIR, "Folders")
        if args.week and args.year:
            target_dir = os.path.join(base_dir, f"week {args.week}")
        else:
            # Default to current week if not specified
            today = datetime.date.today()
            week = today.isocalendar()[1]
            year = today.year
            target_dir = os.path.join(base_dir, f"week {week}")
            
        if os.path.exists(target_dir):
            run_preprocessing(target_dir, force=args.force_preprocess)
        else:
            print(f"No folder found for preprocessing at {target_dir}")

    if args.extract:
        from extract_gemini import run_extraction
        # Determine path
        base_dir = os.path.join(BASE_DIR, "Folders")
        if args.week and args.year:
            target_dir = os.path.join(base_dir, f"week {args.week}")
        else:
            # Default to current week if not specified
            today = datetime.date.today()
            week = today.isocalendar()[1]
            year = today.year
            target_dir = os.path.join(base_dir, f"week {week}")
            
        if os.path.exists(target_dir):
            run_extraction(target_dir, model_name=args.model, debug_mode=args.debug)
        else:
            print(f"No folder found for extraction at {target_dir}")

    if args.visualize:
        from visualize import run_visualization
        # Determine path
        base_dir = os.path.join(BASE_DIR, "Folders")
        if args.week and args.year:
            target_dir = os.path.join(base_dir, f"week {args.week}")
        else:
            today = datetime.date.today()
            week = today.isocalendar()[1]
            year = today.year
            target_dir = os.path.join(base_dir, f"week {week}")
            
        if os.path.exists(target_dir):
            run_visualization(target_dir)

    if args.web:
        from database.web_db import init_web_db, add_web_product, delete_web_products
        from scrapers.dirk_web import DirkWebScraper
        from scrapers.ah_web import AHWebScraper
        from scrapers.aldi_web import AldiWebScraper
        from scrapers.jumbo_web import JumboWebScraper
        from scrapers.hoogvliet_web import HoogvlietWebScraper
        
        init_web_db()
        
        all_web_scrapers = [
            DirkWebScraper(),       # 1
            AHWebScraper(),         # 2
            AldiWebScraper(),       # 3
            JumboWebScraper(),      # 4
            HoogvlietWebScraper(),  # 5
        ]
        
        scrapers_to_run = []
        if not args.stores or '0' in str(args.stores):
            scrapers_to_run = all_web_scrapers
        else:
            indices = set(str(args.stores))
            for char in indices:
                if char.isdigit():
                    idx = int(char) - 1
                    if 0 <= idx < len(all_web_scrapers):
                        scrapers_to_run.append(all_web_scrapers[idx])
            # Sort by original index
            scrapers_to_run.sort(key=lambda s: all_web_scrapers.index(s))
            
        if not scrapers_to_run:
            print("No valid stores selected. Defaulting to ALL.")
            scrapers_to_run = all_web_scrapers
        
        today = datetime.date.today()
        week = args.week if args.week else today.isocalendar()[1]
        year = args.year if args.year else today.year
        
        for scraper in scrapers_to_run:
            # Clear existing data for this store/week to avoid duplicates
            delete_web_products(scraper.store_name, week, year)
            
            products = scraper.scrape(week, year)
            if products:
                print(f"Found {len(products)} deals for {scraper.store_name}")
                for p in products:
                    add_web_product(p)
            else:
                print(f"No deals found for {scraper.store_name}")

