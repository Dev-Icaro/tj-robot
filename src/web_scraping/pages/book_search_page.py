from common.exceptions.app_exception import AppException
from common.constants.tj_site import BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from web_scraping.components.base_component import BaseComponent
from web_scraping.components.calendar import find_calendar
from web_scraping.pages.base_page import BasePage
import re


class BookSearchPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

        if not "Consulta de Diário da Justiça Eletrônico" in self.driver.title:
            self.driver.get(BASE_URL + "/cdje/consultaAvancada.do#buscaavancada")
            self.wait_load()

    book_select_by = (
        By.XPATH,
        "/html/body/table[4]/tbody/tr/td/div[3]/table[2]/tbody/tr/td/form/div/table/tbody/tr[2]/td[2]/table/tbody/tr/td/select",
    )
    keyword_by = (By.ID, "procura")
    calendar_start_by = (By.ID, "trigger2")
    calendar_end_by = (By.ID, "trigger3")
    search_by = (
        By.XPATH,
        '//*[@id="avancado"]/tbody/tr[5]/td[2]/table/tbody/tr/td/input[1]',
    )
    results_by = (By.ID, "divResultadosInferior")

    def select_book(self, option_text):
        select = Select(self.driver.find_element(*self.book_select_by))
        options_text = [option.text for option in select.options]

        if option_text in options_text:
            select.select_by_visible_text(option_text)
        else:
            raise AppException(
                "O Caderno definido para a pesquisa não foi encontrado, por favor selecionar uma opção valida"
            )

        return self

    def set_keyword(self, keywords):
        keywords = " OU ".join(keywords)
        self.driver.find_element(*self.keyword_by).send_keys(keywords)

        return self

    def set_start_date(self, date):
        self.driver.find_element(*self.calendar_start_by).click()
        calendar = find_calendar(self.driver)
        calendar.set_date(date)

        return self

    def set_end_date(self, date):
        self.driver.find_element(*self.calendar_end_by).click()
        calendar = find_calendar(self.driver)
        calendar.set_date(date)

        return self

    def click_search_button(self):
        self.driver.find_element(*self.search_by).click()
        return OccurrencesList(self.driver.find_element(*self.results_by))


class OccurrencesList(BaseComponent):
    def __init__(self, root):
        super().__init__(root)

    occurrences_by = (By.CLASS_NAME, "fundocinza1")
    nav_buttons_by = (By.CSS_SELECTOR, "span.style5 a")
    page_number_by = (By.CSS_SELECTOR, "span.style5 strong")

    def get_occurences(self):
        occurrences = self.root.find_elements(*self.occurrences_by)
        return [Occurrence(item) for item in occurrences]

    def get_page_number(self):
        return self.root.find_element(*self.page_number_by).text.strip()

    def locate_next_button(self):
        nav_buttons = self.root.find_elements(*self.nav_buttons_by)
        for btn in nav_buttons:
            if btn.text == "Próximo>":
                return btn

    def has_next_page(self):
        return True if self.locate_next_button() else False

    def next_page(self):
        self.locate_next_button().click()


class Occurrence(BaseComponent):
    def __init__(self, root):
        super().__init__(root)

    def get_pdf_url(self):
        anchor = self.root.find_elements(By.TAG_NAME, "a")[0]
        regex = r"\('(.*?)'\)"
        endpoint = re.findall(regex, anchor.get_attribute("onclick"))[0]

        return BASE_URL + endpoint.replace("consultaSimples", "getPaginaDoDiario")
