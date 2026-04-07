from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

opts = Options()
opts.add_argument('--headless')
opts.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
service = Service(executable_path=r'C:\geckodriver.exe')
driver = webdriver.Firefox(service=service, options=opts)

print("Navigating to Aldi deals...")
driver.get('https://www.aldi.nl/aanbiedingen.html')
time.sleep(3)

# Click next week
btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Volgende week'].tabs__tab")
if btns:
    driver.execute_script("arguments[0].scrollIntoView(true);", btns[0])
    driver.execute_script("arguments[0].click();", btns[0])
    print("Clicked Volgende week.")
    
    # Wait for the title to change or for articles to show up
    print("Waiting 10s to see if content hydrates...")
    for i in range(10):
        time.sleep(1)
        articles = driver.find_elements(By.CSS_SELECTOR, "article, .mod-article-tile, .tiles-grid__item")
        print(f"Sec {i+1}: Found {len(articles)} deal items.")
else:
    print("Toggle button not found.")

driver.quit()
