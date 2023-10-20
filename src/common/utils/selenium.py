import os, logging
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


def init_driver():
    os.environ["WDM_LOG"] = str(logging.NOTSET)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    return driver


def clear_and_type(element, value):
    element.clear()
    element.send_keys(value)
