from datetime import datetime, timedelta
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from components.calendar import Calendar


def find_calendar(driver):
    calendar = WebDriverWait(driver, 3).until(
        EC.visibility_of_any_elements_located((By.CSS_SELECTOR, "div.calendar"))
    )[0]

    return Calendar(calendar)


def is_date_in_limit(date):
    date_obj = datetime.strptime(date, "%d/%m/%Y")
    cur_date = datetime.now()
    cur_year = cur_date.year
    year_dif = abs(int(date_obj.year - cur_year))

    if year_dif > 15 or date_obj > cur_date:
        return False
    else:
        return True


def calc_valid_calendar_date(self, date):
    date = datetime.strptime(date, "%d/%m/%Y")

    if date.weekday() == 5:
        date = date - timedelta(1)
    elif date.weekday() == 6:
        date = date - timedelta(2)

    return date
