from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.parse

def scrapeSentenceExample(hanzi):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome("D:\Program Files\chromedriver_win32\chromedriver.exe", options=chrome_options)

    try:
        browser.get(buildURL(hanzi))
        return getExampleText(browser)
    finally:
        browser.quit()

def buildURL(hanzi):
    # Only used to return bigram examples of monograms
    url_gtts = 'https://dictionary.writtenchinese.com/'
    # Parse character into UTF-8
    query = urllib.parse.quote(hanzi)
    # Create URL
    return url_gtts + "#sk=" + query + "&svt=pinyin"

def getExampleText(browser):
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "bothTable"))
    )
    word_link = browser.find_element_by_xpath(
        '/html/body/div[2]/section/div/div[3]/div/div[4]/div/div/table/tbody/tr[1]/td[1]/table/tbody/tr/td[3]/a/span')
    word_link.click()

    example_text = browser.find_element_by_class_name('symbol-block')

    soup = BeautifulSoup(example_text.get_attribute('innerHTML'), features="html.parser")

    chinese = ""
    for text in soup.find_all('font'):
        chinese = chinese + text.string

    pinyin = ""
    for text in soup.find_all('span'):
        pinyin = pinyin + text.string + " "

    english = ""
    for text in soup.find_all('p'):
        english = english + text.string + " "

    return(chinese + pinyin + english)