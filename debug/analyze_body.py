from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time

opts = Options()
opts.add_argument('--headless')
opts.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
service = Service(executable_path=r'C:\geckodriver.exe')
driver = webdriver.Firefox(service=service, options=opts)

driver.get('https://www.aldi.nl/aanbiedingen/wk16_vanaf_maandag_14_04.html') # or something?
# Actually let's just do exactly what we did before
driver.get('https://www.aldi.nl/aanbiedingen.html')
time.sleep(3)

# Click next week
btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Volgende week'].tabs__tab")
if btns:
    driver.execute_script("arguments[0].scrollIntoView(true);", btns[0])
    driver.execute_script("arguments[0].click();", btns[0])
    time.sleep(5)
    
    # print text of body
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print(body_text[:1000])
    
    page = driver.page_source
    print("Has article?", 'article' in page.lower())
    print("Has mod-article-tile?", 'mod-article-tile' in page.lower())
    
driver.quit()
