from common.constants.tj_site import CASE_SEARCH_URL
from web_scraping.pages.case_search_page import CaseSearchPage


def load_case_page(self, case_number):
    self.driver.get(CASE_SEARCH_URL)
    search_page = CaseSearchPage(self.driver)
    return search_page.search_case(case_number)
