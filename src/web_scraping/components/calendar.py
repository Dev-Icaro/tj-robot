from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.utils.string import extract_letters, extract_numbers
from common.utils.date import is_valid_date
from common.exceptions.app_exception import (
    AppException,
    InvalidArgumentException,
    InvalidDateException,
    RequiredArgumentException,
)
from web_scraping.common.exceptions import DisabledCalendarDateException
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
            raise AppException("Elemento calendário inválido")

        self.navigation = CalendarNavigation(
            self.root.find_element(By.CLASS_NAME, "headrow")
        )
        self.title_by = (By.CLASS_NAME, "title")
        self.day_button_by = (By.CSS_SELECTOR, "tbody > tr.daysrow td.day")

    def set_date(self, date):
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%d/%m/%Y")
        elif isinstance(date, datetime):
            date_obj = date
        else:
            raise InvalidArgumentException(
                "Tipagem de 'date' inválida em set_date em Calendar"
            )

        self.validate_date(date)

        self.set_year(date_obj.year)
        self.set_month(date_obj.month)
        self.set_day(date_obj.day)

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

    def set_day(self, day):
        day_btn = self.locate_day_button(day)
        if day_btn.is_disabled():
            raise DisabledCalendarDateException(
                "O Botão do dia selecionado, no calendário, está desabilitado."
            )

        day_btn.click()

    def get_day_buttons(self):
        day_buttons = self.root.find_elements(*self.day_button_by)
        return [CalendarDayButton(btn) for btn in day_buttons]

    def locate_day_button(self, day):
        day_buttons = self.get_day_buttons()
        for day_btn in day_buttons:
            if int(day_btn.get_text()) == day:
                return day_btn

    def validate_date(self, date):
        if isinstance(date, datetime):
            date = date.strftime("%d/%m/%Y")

        if not date:
            raise RequiredArgumentException("Parâmetro requerido:", date)

        if not is_valid_date(date):
            raise InvalidDateException(
                "Data inválida para ao selecionar data do calendário."
            )

        if not is_date_in_limit(date):
            raise InvalidDateException("Data fora do limite do calendário do TJ.")


class CalendarNavigation(BaseComponent):
    def __init__(self, root):
        super().__init__(root)
        if self.root is None:
            raise AppException("Navegação do calendário não encontrada.")

        self.buttons = self.root.find_elements(By.CSS_SELECTOR, "td.button.nav")

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


class CalendarDayButton(BaseComponent):
    def __init__(self, root):
        super().__init__(root)

    def get_text(self):
        return self.root.text

    def get_class(self):
        return self.root.get_attribute("class").split()

    def is_disabled(self):
        return "disabled" in self.get_class()

    def click(self):
        self.root.click()
        return self


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
