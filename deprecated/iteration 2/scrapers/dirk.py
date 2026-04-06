from .base import Scraper
from playwright.sync_api import sync_playwright
import os
import time

class DirkScraper(Scraper):
    def __init__(self, base_dir):
        super().__init__("Dirk", base_dir)

    def scrape(self, week, year, force=False):
        from PIL import Image
        
        url = "https://www.dirk.nl/folder"
        save_dir = self.get_store_dir(week, year)
        pdf_filename = f"Dirk_week_{week}_{year}.pdf"
        pdf_path = os.path.join(save_dir, pdf_filename)
        
        # Check if we already have the PDF
        if os.path.exists(pdf_path) and not force:
            print(f"Dirk flyer for week {week} already exists.")
            return pdf_path

        print(f"Scraping Dirk folder from {url}")
        
        downloaded_images = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            
            # Wait for images to load
            try:
                page.wait_for_selector('.publication-images img', timeout=10000)
            except:
                print("Could not find Dirk images.")
                browser.close()
                return None
            
            # Scroll down to load all lazy-loaded images
            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Extract image URLs
            images = page.query_selector_all('.publication-images img')
            image_urls = [img.get_attribute('src') for img in images]
            
            print(f"Found {len(image_urls)} images for Dirk.")
            
            for i, img_url in enumerate(image_urls):
                if img_url:
                    # Clean up URL if needed (remove query params)
                    clean_url = img_url.split('?')[0]
                    ext = os.path.splitext(clean_url)[1] or '.jpg'
                    filename = f"dirk_page_{i+1}{ext}"
                    filepath = os.path.join(save_dir, filename)
                    self.download_file(img_url, filepath)
                    downloaded_images.append(filepath)
            
            browser.close()
            
        # Convert images to PDF (Simple Stitch)
        if downloaded_images:
            print("Converting images to PDF...")
            try:
                pil_images = []
                for img_path in downloaded_images:
                    try:
                        img = Image.open(img_path).convert('RGB')
                        pil_images.append(img)
                    except Exception as e:
                        print(f"Error reading image {img_path}: {e}")

                if pil_images:
                    pil_images[0].save(pdf_path, save_all=True, append_images=pil_images[1:])
                    print(f"Saved PDF to {pdf_path}")
                    
                    # Clean up individual images
                    for img_path in downloaded_images:
                        try:
                            os.remove(img_path)
                        except:
                            pass
                    print("Cleaned up individual images.")
                    return pdf_path
            except Exception as e:
                print(f"Error converting to PDF: {e}")
                return save_dir # Return dir as fallback if PDF fails
                
        return None
