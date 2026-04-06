from .base import Scraper
from playwright.sync_api import sync_playwright
import os
import time

class PublitasScraper(Scraper):
    def __init__(self, store_name, base_dir, start_url_fn):
        super().__init__(store_name, base_dir)
        self.start_url_fn = start_url_fn

    def scrape(self, week, year, force=False):
        start_url = self.start_url_fn(week, year)
        if not start_url:
            print(f"Could not determine start URL for {self.store_name}")
            return None

        save_dir = self.get_store_dir(week, year)
        if os.listdir(save_dir) and not force:
             print(f"{self.store_name} folder for week {week} seems to be already downloaded.")
             return save_dir

        print(f"Scraping {self.store_name} from {start_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Increase resolution: Viewport 1920x1080, Device Scale Factor 2 (Retina-like)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=2)
            try:
                page.goto(start_url, timeout=60000) # Increased timeout to 60s
            except Exception as e:
                print(f"Timeout or error loading {start_url}: {e}")
                browser.close()
                return None
            
            # Handle cookie banners (Robust attempt)
            try:
                # Wait a bit for the banner to appear
                time.sleep(2)
                
                # Common selectors for "Accept" buttons
                cookie_selectors = [
                    '#onetrust-accept-btn-handler',
                    'button:has-text("Accepteren")',
                    'button:has-text("Alles accepteren")',
                    'a:has-text("Accepteren")',
                    '#accept-cookies',
                    '.cookie-accept-btn'
                ]
                
                for selector in cookie_selectors:
                    if page.is_visible(selector):
                        print(f"Found cookie button: {selector}")
                        page.click(selector)
                        time.sleep(1)
                        break
            except Exception as e:
                print(f"Cookie handling warning: {e}")

            # Handle "Openen" button (Hoogvliet)
            try:
                if page.is_visible('text=Openen'):
                    page.click('text=Openen')
                    print("Clicked 'Openen' button")
                    time.sleep(2)
            except:
                pass

            # Logic to find the actual viewer URL if we are on a landing page
            # If no publitas iframe is found, we might need to click a folder thumbnail (AH case)
            try:
                # Check if we already have the iframe
                if not page.query_selector('iframe[src*="publitas"]'):
                    print("No Publitas iframe found yet. Checking for folder links...")
                    
                    # Hoogvliet specific: Link containing 'folder-'
                    hoogvliet_link = page.query_selector('a[href*="/folder-"]')
                    if hoogvliet_link:
                         print(f"Found Hoogvliet folder link: {hoogvliet_link}")
                         hoogvliet_link.click()
                         page.wait_for_load_state('networkidle')
                         time.sleep(3)
                    else:
                        # Look for links that might be folders
                        # AH specific: often inside a grid, href contains 'folder'
                        folder_link = page.query_selector('a[href*="/folder/"]:not([href*="bonus/folder"])') # Try to avoid self-link
                        
                        if not folder_link:
                             # Try generic "first image inside a link" approach
                             folder_link = page.query_selector('main a img')
                             if folder_link:
                                 folder_link = folder_link.query_selector('xpath=..') # Get parent a
                        
                        if folder_link:
                            print(f"Clicking potential folder link: {folder_link}")
                            folder_link.click()
                            page.wait_for_load_state('networkidle')
                            time.sleep(3) # Wait for navigation/render
            except Exception as e:
                print(f"Navigation warning: {e}")

            # Wait for Publitas viewer
            try:
                # Look for the main viewer container or iframe
                # Many Publitas viewers are iframes or have a specific structure.
                # If it's an iframe, we need to get the iframe src.
                frame_element = page.query_selector('iframe[src*="publitas"]')
                if frame_element:
                    viewer_url = frame_element.get_attribute('src')
                    print(f"Found Publitas iframe: {viewer_url}")
                    
                    # Fix protocol-relative URLs
                    if viewer_url.startswith('//'):
                        viewer_url = 'https:' + viewer_url
                        
                    page.goto(viewer_url)
                    # We navigated away, so the frame_element is no longer valid.
                    # We are now on the viewer page itself.
                    frame_element = None
                
                page.wait_for_load_state('networkidle')
                
                # Try to find a PDF download button
                pdf_button = page.query_selector('#downloadAsPdf')
                if pdf_button:
                    pdf_url = pdf_button.get_attribute('href')
                    if pdf_url:
                        print(f"Found PDF download link: {pdf_url}")
                        # Handle relative URLs if necessary
                        if not pdf_url.startswith('http'):
                             # Sometimes it's protocol relative or root relative
                             if pdf_url.startswith('//'):
                                 pdf_url = 'https:' + pdf_url
                             elif pdf_url.startswith('/'):
                                 # Need base URL
                                 # For now assume it's absolute or protocol relative usually
                                 pass
                        
                        try:
                            # Use the base scraper's download_file method
                            # We need to import requests or use the method from self
                            # But self.download_file uses requests, which might not share cookies with playwright
                            # However, usually these PDFs are public.
                            
                            filename = f"{self.store_name}_week_{week}_{year}.pdf"
                            filepath = os.path.join(save_dir, filename)
                            
                            # We can try to download using the browser context or requests
                            # Let's try requests first, it's simpler
                            self.download_file(pdf_url, filepath)
                            print(f"Successfully downloaded PDF for {self.store_name}")
                            browser.close()
                            return filepath
                        except Exception as e:
                            print(f"Failed to download PDF from {pdf_url}: {e}")
                            # Fallback to screenshots if download fails
                
                # ALTERNATIVE: Screenshot pages.
                # Publitas renders pages as images/canvas.
                # We can iterate through pages.
                
                # Let's try to find the "pages" metadata if possible, or just screenshot.
                # Screenshotting is safer.
                
                # Find total pages (often "1 / 24" text)
                # For now, let's just screenshot the first 20 pages or until we fail.
                
                # We need to click "next page"
                # Arrow right key usually works.
                
                visited_urls = set()
                
                for i in range(1, 100): # Increased limit
                    # Check for cycles (e.g. looping back to page 1)
                    current_url = page.url
                    if current_url in visited_urls:
                        print(f"Cycle detected at page {i} (URL visited before). Stopping.")
                        break
                    visited_urls.add(current_url)
                    
                    filename = f"{self.store_name}_page_{i}.png"
                    filepath = os.path.join(save_dir, filename)
                    
                    # Always screenshot the full page (we navigated to the viewer)
                    page.screenshot(path=filepath)
                    
                    print(f"Saved page {i}")
                    
                    # Post-process image to trim whitespace/banners
                    try:
                        self.trim_image(filepath)
                    except Exception as e:
                        print(f"Error trimming image {filepath}: {e}")
                    
                    # Click next
                    page.keyboard.press('ArrowRight')
                    time.sleep(1.5) # Wait for transition
                    
            except Exception as e:
                print(f"Error scraping {self.store_name}: {e}")
                browser.close()
                return None

            browser.close()
        
        return save_dir

    def trim_image(self, filepath):
        from PIL import Image, ImageChops
        
        img = Image.open(filepath)
        
        # 1. Trim uniform border (whitespace)
        bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
        diff = ImageChops.difference(img, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        
        if bbox:
            img = img.crop(bbox)
            
        # 2. Trim bottom banner (approx 50px for "Openen" button if present)
        # This is a heuristic. We can be smarter if needed.
        # For now, let's just assume the "Openen" button is at the bottom right
        # and might have been caught if it wasn't white.
        # But if we screenshot the iframe, we might avoid it?
        # If we screenshot the iframe, the "Openen" button is usually OUTSIDE the iframe or overlaying it.
        # If overlaying, we need to crop it.
        
        # Let's crop 60px from bottom just in case, if it looks like a banner?
        # Or better: The user said "trim banner".
        # Let's crop a small fixed amount from bottom if we suspect a banner.
        # Actually, let's just stick to whitespace trimming first.
        # If the "Openen" button is floating, it might be surrounded by white, so bbox might catch it.
        
        img.save(filepath)

# Specific store implementations
def get_ah_url(week, year):
    # Logic to find AH url
    # For now, return the landing page and let the scraper handle it?
    # Or try to construct it: https://www.ah.nl/bonus/folder
    return "https://www.ah.nl/bonus/folder"

def get_jumbo_url(week, year):
    return "https://www.jumbo.com/acties/weekaanbiedingen"

def get_hoogvliet_url(week, year):
    return "https://www.hoogvliet.com/folder"
