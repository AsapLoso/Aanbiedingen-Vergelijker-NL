from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import time

opts = Options()
opts.add_argument('--headless')
opts.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
service = Service(executable_path=r'C:\geckodriver.exe')
driver = webdriver.Firefox(service=service, options=opts)

driver.get('https://www.hoogvliet.com/aanbiedingen')
time.sleep(5)
html = driver.page_source
soup = BeautifulSoup(html, 'lxml')

# Look for tabs or things that might indicate date periods
elements = soup.find_all(lambda tag: tag.name in ['a', 'button', 'li', 'span', 'label'] and any(word in tag.get_text().lower() for word in ['volgende', 'week', 'vanaf']))
for el in elements:
    print(f"Tag: {el.name}, Class: {el.get('class')}, ID: {el.get('id')}, Text: {el.get_text().strip()}")

driver.quit()
