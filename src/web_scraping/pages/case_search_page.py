from web_scraping.pages.base_page import BasePage
from web_scraping.pages.case_page import CasePage
from common.utils.string import extract_numbers
from common.utils.selenium import clear_and_type
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class CaseSearchPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

    case_number_input_by = (By.ID, "numeroDigitoAnoUnificado")
    forum_number_input_by = (By.ID, "foroNumeroUnificado")
    search_button_by = (By.ID, "botaoConsultarProcessos")

    def type_case_number(self, case_number):
        self.wait.until(
            EC.presence_of_element_located(self.case_number_input_by)
        ).send_keys(extract_numbers(case_number))

    def type_forum_number(self, forum_number):
        forum_number_input = self.wait.until(
            EC.presence_of_element_located(self.forum_number_input_by)
        )
        clear_and_type(forum_number_input, extract_numbers(forum_number))

    def submit_search(self):
        self.wait.until(EC.element_to_be_clickable(self.search_button_by)).click()
        return CasePage(self.driver)

    def search_case(self, case_number):
        case_numbers = extract_numbers(case_number)[:13]
        forum_number = case_number[-4:]

        self.type_case_number(case_numbers)
        self.type_forum_number(forum_number)
        return self.submit_search()
