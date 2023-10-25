from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from web_scraping.components.calendar import Calendar
import selenium.webdriver.support.expected_conditions as EC


def find_calendar(driver):
    calendar = WebDriverWait(driver, 3).until(
        EC.visibility_of_any_elements_located((By.CSS_SELECTOR, "div.calendar"))
    )[0]

    return Calendar(calendar)


def calc_valid_calendar_date(date):
    date = datetime.strptime(date, "%d/%m/%Y")

    if date.weekday() == 5:
        date = date - timedelta(1)
    elif date.weekday() == 6:
        date = date - timedelta(2)

    return date
