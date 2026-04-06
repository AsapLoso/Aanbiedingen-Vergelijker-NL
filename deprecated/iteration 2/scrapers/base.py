import os
import requests

class Scraper:
    """
    Base class for legacy PDF/OCR-based scrapers.
    Provides utility methods for directory management and file downloading.
    """
    def __init__(self, store_name, base_dir):
        self.store_name = store_name
        self.base_dir = base_dir

    def get_store_dir(self, week, year):
        """
        Creates and returns the directory for the given store and week.
        Structure: BASE_DIR/Folders/week {week}/{store_name}
        """
        store_dir = os.path.join(self.base_dir, "Folders", f"week {week}", self.store_name)
        os.makedirs(store_dir, exist_ok=True)
        return store_dir

    def download_file(self, url, filepath):
        """
        Downloads a file from the given URL to the specified filepath.
        Returns the filepath on success, None on failure.
        """
        try:
            print(f"  -> Downloading: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  -> Success: {filepath}")
            return filepath
        except Exception as e:
            print(f"  -> Error downloading {url}: {e}")
            return None
