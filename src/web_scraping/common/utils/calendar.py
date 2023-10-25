from datetime import datetime, timedelta
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from web_scraping.components.calendar import Calendar


def find_calendar(driver):
    calendar = WebDriverWait(driver, 3).until(
        EC.visibility_of_any_elements_located((By.CSS_SELECTOR, "div.calendar"))
    )[0]

    return Calendar(calendar)


def calc_valid_calendar_date(self, date):
    date = datetime.strptime(date, "%d/%m/%Y")

    if date.weekday() == 5:
        date = date - timedelta(1)
    elif date.weekday() == 6:
        date = date - timedelta(2)

    return date
