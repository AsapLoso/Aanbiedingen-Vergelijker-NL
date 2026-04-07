import os
import sys

# Setup paths for imports
project_root = r"c:\Users\Deuts\OneDrive - Delft University of Technology\Misc\Gemini\Boodschappen"
sys.path.append(project_root)

from scraper.web_scraper import SnapshotManager
from scraper.html_parser import DealParser

print("🤖 Testing Aldi 'next' extraction...")
sm = SnapshotManager(headless=True)
filepath = sm.capture("aldi", period="next")

if filepath:
    print(f"\n✅ HTML Snapshot saved to: {filepath}")
    parser = DealParser()
    deals = parser.parse(filepath)
    print(f"🔍 Parsed {len(deals)} deals.")
    if len(deals) > 0:
        print("Sample deal:", deals[0])
    
    # Read the file size
    size = os.path.getsize(filepath) / 1024
    print(f"📄 File size: {size:.2f} KB")
else:
    print("❌ Failed to capture Aldi.")
