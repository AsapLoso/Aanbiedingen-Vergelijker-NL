"""
web_scraper.py — Selenium-based HTML Snapshot Fetcher

Navigates to each supermarket's deals page, accepts cookies,
scrolls to load all content, and saves the full page HTML to data/raw/.

Does NOT parse anything — that's html_parser.py's job.
"""

import os
import re
import time
import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ── Store configurations ─────────────────────────────────────────────
STORES = {
    "dirk": {
        "name": "Dirk",
        "url": "https://www.dirk.nl/aanbiedingen",
        "needs_reload": False,
        "scroll_pause": 1.5,
        "multi_page": False,
    },
    "ah": {
        "name": "Albert Heijn",
        "url": "https://www.ah.nl/bonus",
        "needs_reload": True,       # AH is bot-proof, needs reload trick
        "scroll_pause": 1.5,
        "multi_page": False,
    },
    "aldi": {
        "name": "Aldi",
        "url": "https://www.aldi.nl/aanbiedingen.html",
        "needs_reload": False,
        "scroll_pause": 1.5,
        "multi_page": False,
    },
    "jumbo": {
        "name": "Jumbo",
        "url": "https://www.jumbo.com/aanbiedingen/nu",
        "needs_reload": False,
        "scroll_pause": 1.0,
        "multi_page": True,         # Jumbo needs individual product page visits
    },
    "hoogvliet": {
        "name": "Hoogvliet",
        "url": "https://www.hoogvliet.com/aanbiedingen",
        "needs_reload": False,
        "scroll_pause": 2.0,
        "multi_page": False,
        "remove_selectors": ["footer", "#cookie-consent-shadow-bg", "#cookie-consent-cookie-bar-center"],
    },
}


class SnapshotManager:
    """
    Captures HTML snapshots of supermarket deal pages.
    
    Usage:
        sm = SnapshotManager(headless=False)
        filepath = sm.capture("dirk")
        # => data/raw/dirk_2026-04-05.html
    """

    def __init__(self, headless=True):
        self.headless = headless
        self.raw_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

    def _make_driver(self):
        """Create a Firefox WebDriver instance."""
        opts = Options()
        opts.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        if self.headless:
            opts.add_argument("--headless")
        opts.set_preference("general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
            "Gecko/20100101 Firefox/120.0")
        # Use geckodriver at C:\geckodriver.exe
        service = Service(executable_path=r"C:\geckodriver.exe")
        driver = webdriver.Firefox(service=service, options=opts)
        driver.set_window_size(1920, 1080)
        return driver

    def capture(self, store_key, period="current"):
        """
        Capture a snapshot for a given store and period.
        
        Args:
            store_key: 'dirk', 'ah', 'aldi', 'jumbo', 'hoogvliet'
            period: 'current' or 'next'
            
        Returns:
            filepath (str) on success, None on failure.
        """
        if store_key not in STORES:
            print(f"❌ Unknown store: {store_key}")
            return None

        config = STORES[store_key]
        print(f"\n🚀 Capturing {config['name']} ({period})...")
        driver = self._make_driver()

        try:
            driver.get(config["url"])
            time.sleep(3)
            self._accept_cookies(driver)

            # ── AH anti-bot ──
            if config["needs_reload"]:
                print("   ⏳ AH anti-bot: waiting 5s before reload...")
                time.sleep(5)
                driver.refresh()
                print("   ⏳ Waiting 5s after reload...")
                time.sleep(5)
                self._accept_cookies(driver)  # cookie banner may reappear

            # ── Period Toggling ──
            if period == "next":
                self._toggle_to_next_week(driver, store_key)

            # ── Jumbo: multi-page capture ──
            if config["multi_page"]:
                return self._capture_jumbo(driver, config)

            # ── Standard: scroll + save ──
            # Remove blocking elements if configured (e.g. Hoogvliet footer)
            if "remove_selectors" in config:
                selectors = ", ".join([f'"{s}"' for s in config["remove_selectors"]])
                js = f'document.querySelectorAll([{selectors}]).forEach(el => el.remove());'
                driver.execute_script(js)
                print(f"   🧹 Removed blocking elements: {config['remove_selectors']}")
                time.sleep(1)

            print("   📜 Scrolling to load all deals...")
            self._scroll_to_bottom(driver, pause=config["scroll_pause"])

            return self._save_html(driver, store_key, period=period)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
        finally:
            driver.quit()

    def _capture_jumbo(self, driver, config):
        """
        Jumbo special case: scroll the listing page, collect product links,
        then visit each one and save individual HTMLs.
        """
        print("   📜 Scrolling listing page...")
        # Jumbo uses slow incremental scrolling
        for _ in range(15):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(config["scroll_pause"])

        # Collect product links
        print("   🔗 Collecting product links...")
        anchors = driver.find_elements(By.TAG_NAME, "a")
        hrefs = set()
        for a in anchors:
            href = a.get_attribute("href") or ""
            if "/producten/" in href or "/aanbiedingen/" in href:
                # Must end with an ID pattern (digits, possibly with letters)
                if re.search(r'[-/][0-9]+[A-Z0-9]*$', href):
                    hrefs.add(href)

        product_links = sorted(hrefs)
        print(f"   Found {len(product_links)} unique product links.")

        if not product_links:
            print("   ⚠️ No product links found, saving listing page as fallback.")
            return self._save_html(driver, "jumbo")

        # Save listing page
        self._save_html(driver, "jumbo_listing")

        # Create subfolder for individual pages
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        jumbo_dir = os.path.join(self.raw_dir, f"jumbo_{date_str}")
        os.makedirs(jumbo_dir, exist_ok=True)

        # Visit each product page and save
        for i, link in enumerate(product_links):
            try:
                print(f"   [{i+1}/{len(product_links)}] {link[:80]}...")
                driver.get(link)
                time.sleep(1.5)

                # Save individual page
                slug = link.rstrip("/").split("/")[-1][:50]
                filepath = os.path.join(jumbo_dir, f"{slug}.html")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)

            except Exception as e:
                print(f"   ⚠️ Error on {link}: {e}")

        print(f"   ✅ Saved {len(product_links)} Jumbo product pages to {jumbo_dir}")
        return jumbo_dir

    def _toggle_to_next_week(self, driver, store_key):
        """Find and click the 'next week' or future period button/tab."""
        print(f"   📅 Toggling to next week for {store_key}...")
        try:
            if store_key == "hoogvliet":
                # The sidebar has two date labels. Click the 2nd one.
                labels = driver.find_elements(By.CSS_SELECTOR, "label.filter-checkbox-label")
                if len(labels) >= 2:
                    driver.execute_script("arguments[0].click();", labels[1])
                    time.sleep(2)

            elif store_key == "ah":
                # Click toggle, then wait for radio
                # Use JS click because this element is often obscured or tricky
                toggle = driver.find_element(By.ID, "period-toggle-button")
                driver.execute_script("arguments[0].scrollIntoView(true);", toggle)
                driver.execute_script("arguments[0].click();", toggle)
                time.sleep(1.5)
                
                # Selection of the radio button
                radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                if len(radios) >= 2:
                    # Click the 2nd one (usually next week)
                    driver.execute_script("arguments[0].click();", radios[1])
                    time.sleep(3)

            elif store_key == "dirk":
                # Click the calender-button that says 'vanaf'
                btns = driver.find_elements(By.CSS_SELECTOR, "button.calender-button")
                for btn in btns:
                    if "vanaf" in btn.text.lower():
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        break

            elif store_key == "aldi":
                # Find button with text "Volgende week" -> try multiple methods
                try:
                    # Try finding by text in button
                    btn = driver.execute_script("""
                        return Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Volgende week'));
                    """)
                    if btn:
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        driver.execute_script("arguments[0].click();", btn)
                    else:
                        # Fallback to general XPath if JS fails
                        btn = driver.find_element(By.XPATH, "//button[contains(., 'Volgende week')]")
                        btn.click()
                    
                    # Wait for products to load or transition
                    time.sleep(5)
                except Exception as ex:
                    print(f"      ⚠️ Aldi toggle failed: {ex}")

            elif store_key == "jumbo":
                # Jumbo toggle using the aria-label
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Wissel van periode']")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                except:
                    # Maybe it's on a listing page?
                    pass

        except Exception as e:
            print(f"   ⚠️ Could not toggle {store_key} to next week: {e}")

    def _accept_cookies(self, driver):
        """Try common cookie acceptance buttons."""
        selectors = [
            "#onetrust-accept-btn-handler",
            "#accept-cookies",
            "button.cookie-accept-btn",
        ]
        # XPath for Dutch text buttons
        xpaths = [
            "//button[contains(text(), 'Accepteren')]",
            "//button[contains(text(), 'Alles accepteren')]",
            "//a[contains(text(), 'Accepteren')]",
            "//button[contains(@aria-label, 'Accepteer')]",
        ]

        for sel in selectors:
            try:
                btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                btn.click()
                print(f"   🍪 Accepted cookies via: {sel}")
                time.sleep(1)
                return True
            except:
                pass

        for xp in xpaths:
            try:
                btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                btn.click()
                print(f"   🍪 Accepted cookies via XPath")
                time.sleep(1)
                return True
            except:
                pass

        print("   🍪 No cookie banner found (or already accepted)")
        return False

    def _scroll_to_bottom(self, driver, pause=2.0, max_scrolls=100):
        """Scroll to the bottom of the page to trigger lazy loading.
        Also attempts to click 'Show more' buttons if they appear.
        """
        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        
        # Dutch "Show more" labels
        show_more_text = ["Toon meer", "Bekijk meer", "Laad meer"]
        
        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            
            # Check if height changed
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # If height didn't change, try to find and click a "Show more" button
            if new_height == last_height:
                clicked = False
                for text in show_more_text:
                    try:
                        # Find buttons containing the text
                        xpath = f"//button[contains(text(), '{text}')] | //a[contains(text(), '{text}')]"
                        btn = driver.find_element(By.XPATH, xpath)
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"   🖱️ Clicked '{text}' button")
                            time.sleep(pause * 1.5)
                            new_height = driver.execute_script("return document.body.scrollHeight")
                            clicked = True
                            break
                    except:
                        pass
                
                if not clicked:
                    # Final attempt: small extra wait to see if it's just slow
                    time.sleep(pause)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
            
            last_height = new_height
            scrolls += 1
            
        print(f"   Scrolled/updated {scrolls} times.")

    def _save_html(self, driver, store_key, period="current"):
        """Save the current page source to data/raw/."""
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"{store_key}_{period}_{date_str}.html"
        filepath = os.path.join(self.raw_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        size_kb = os.path.getsize(filepath) / 1024
        print(f"   ✅ Saved {filepath} ({size_kb:.0f} KB)")
        return filepath


def capture_all(headless=True):
    """Capture snapshots for all stores."""
    sm = SnapshotManager(headless=headless)
    results = {}
    for key in STORES:
        results[key] = sm.capture(key)
    return results


if __name__ == "__main__":
    # Quick test: capture Dirk (simplest store)
    sm = SnapshotManager(headless=False)
    sm.capture("dirk")
