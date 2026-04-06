import abc
import datetime
import time
from playwright.sync_api import sync_playwright

class WebScraper(abc.ABC):
    def __init__(self, store_name, headless=True):
        self.store_name = store_name
        self.headless = headless

    def get_week_number(self):
        today = datetime.date.today()
        return today.isocalendar()[1]

    def get_year(self):
        return datetime.date.today().year

    def scrape(self, week, year):
        print(f"Starting web scrape for {self.store_name} (Week {week}, {year})")
        products = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless) # Set to False for debugging if needed
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            try:
                products = self.parse_deals(page)
            except Exception as e:
                print(f"Error scraping {self.store_name}: {e}")
            finally:
                browser.close()
                
        return products

    @abc.abstractmethod
    def parse_deals(self, page):
        """
        Navigate to the page, handle cookies, scroll, and extract deals.
        Returns a list of dictionaries.
        """
        pass

    def scroll_to_bottom(self, page, delay=1.0):
        """
        Scrolls to the bottom of the page to trigger lazy loading.
        """
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(delay)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
    def accept_cookies(self, page):
        """
        Tries to accept cookies using common selectors.
        """
        cookie_selectors = [
            '#onetrust-accept-btn-handler',
            'button:has-text("Accepteren")',
            'button:has-text("Alles accepteren")',
            'a:has-text("Accepteren")',
            '#accept-cookies',
            '.cookie-accept-btn',
            '[aria-label="Accepteer cookies"]',
            'button[class*="cookie"]'
        ]
        
        for selector in cookie_selectors:
            try:
                if page.is_visible(selector, timeout=2000):
                    print(f"Found cookie button: {selector}")
                    page.click(selector)
                    time.sleep(1)
                    return True
            except:
                pass
        return False
