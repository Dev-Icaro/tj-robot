from web_scraping.pages.case_page import CasePage
from selenium.webdriver.common.by import By
import re


class IncidentCasePage(CasePage):
    def __init__(self, driver):
        super().__init__(driver)

    case_number_by = (By.CSS_SELECTOR, "#containerDadosPrincipaisProcesso .unj-larger")

    def get_case_number(self):
        element_text = self.driver.find_element(*self.case_number_by).text.strip()
        # regex = r"^Precatório \((\S+?)\)"
        regex = r" \((\S+?)\)"
        match = re.search(regex, element_text)
        if match:
            return match.group(1)
