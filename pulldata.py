import pandas as pd
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import string
import time
pd.options.display.float_format = '{:.0f}'.format

def get_link(ticker):
    str1 = 'https://finance.yahoo.com/quote/' & ticker
    str2 = '/financials?p=' & ticker
    str = str1 & str2
    return str

def main():
    driver = webdriver.Chrome("C:\webdrivers\chromedriver.exe")

    get_link("AAPL")
    driver.get("https://finance.yahoo.com/")
    time.sleep(2)

    driver.find_element_by_xpath("//span[text() = 'Apr 15, 2022 - Apr 20, 2022']").click()
    time.sleep(2)
