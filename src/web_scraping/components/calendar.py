from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.utils.string import extract_letters, extract_numbers
from common.exceptions.app_exception import AppException
from web_scraping.components.base_component import BaseComponent

calendar_months = {
    "Janeiro": 1,
    "Fevereiro": 2,
    "Março": 3,
    "Abril": 4,
    "Maio": 5,
    "Junho": 6,
    "Julho": 7,
    "Agosto": 8,
    "Setembro": 9,
    "Outubro": 10,
    "Novembro": 11,
    "Dezembro": 12,
}

class Calendar(BaseComponent):
    def __init__(self, root):
        super().__init__(root)
        if root is None:
            raise AppException('Elemento calendário inválido')

        self.navigation = CalendarNavigation(self.root.find_element(By.CLASS_NAME, "headrow"))        

        self.title_by = (By.CLASS_NAME, "title")
        self.days_by = (By.CSS_SELECTOR, ''"tbody > tr.daysrow td.day")

    def set_date(self, date):
        date_obj = datetime.strptime(date, "%d/%m/%Y")

        self.set_year(date_obj.year)
        self.set_month(date_obj.month)
        self.set_day(date_obj)

    def get_year(self):
        title = self.root.find_element(*self.title_by).text
        return extract_numbers(title)

    def get_month(self):
        title = self.root.find_element(*self.title_by).text
        return extract_letters(title)

    def set_year(self, year):
        actual_year = int(self.get_year())
        if actual_year == year:
            return
        
        year_dif = abs(year - actual_year)
        while year_dif > 0:
            if actual_year < year:
                self.navigation.next_year()
            else:
                self.navigation.prev_year()

            year_dif -= 1

    def set_month(self, month):
        actual_month = int(calendar_months[self.get_month()])
        if actual_month == month:
            return
        
        month_dif = abs(month - actual_month)
        while month_dif > 0:
            if actual_month < month:
                self.navigation.next_month()
            else:
                self.navigation.prev_month()

            month_dif -= 1

    def set_day(self, obj_date):
        days = self.root.find_elements(*self.days_by)
        for day in days:
            day.classes = day.get_attribute("class").split()

            if day.text == str(obj_date.day):
                if "disabled" in day.classes:
                    previous_date = obj_date - timedelta(1)
                    self.set_date(previous_date.strftime("%d/%m/%Y"))
                else:
                    day.click()
                    return
                

class CalendarNavigation(BaseComponent):
    def __init__(self, root):
        super().__init__(root)
        if self.root is None:
            raise AppException('Navegação do calendário não encontrada')

        self.buttons = self.root.find_elements(
            By.CSS_SELECTOR, "td.button.nav"
        )

    def locate_btn_by_text(self, text):
        for btn in self.buttons:
            if btn.text == text:
                return btn

    def next_month(self):
        self.locate_btn_by_text("›").click()

    def prev_month(self):
        self.locate_btn_by_text("‹").click()

    def next_year(self):
        self.locate_btn_by_text("»").click()

    def prev_year(self):
        self.locate_btn_by_text("«").click()


def find_calendar(driver):
    calendar = WebDriverWait(driver, 3).until(
        EC.visibility_of_any_elements_located((By.CSS_SELECTOR, "div.calendar"))
    )[0]

    return Calendar(calendar)
