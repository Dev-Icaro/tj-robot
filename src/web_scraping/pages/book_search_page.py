from common.utils.string import remove_accents
from common.utils.pdf import fetch_pdf_text_from_url
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from common.utils.logger import logger
from common.exceptions.app_exception import AppException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from web_scraping.components.base_component import BaseComponent
from web_scraping.components.calendar import find_calendar
from web_scraping.pages.base_page import BasePage

import re

TJ_BASE_URL = "https://esaj.tjsp.jus.br"
PDF_ELEMENT_XPATH = "/html/body/embed"
PAGES_RESULT_ELEMENT_XPATH = '//*[@id="divResultadosSuperior"]/table/tbody/tr[1]/td[1]'

class BookSearchPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

        if not 'Consulta de Diário da Justiça Eletrônico' in self.driver.title:
            self.driver.get(TJ_BASE_URL + '/cdje/consultaAvancada.do#buscaavancada')
            self.wait_load()

        self.case_number_regex = re.compile(
            r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2,4}\.\d{4}"
        )

        self.case_blocks_regex = re.compile(
            r"(?:\n+Processo\s+\d+|^Processo\s+\d+|\n+No\s+\d+|^No\s+\d+)[\s\S]*?(?=\-\s+ADV|\Z)",
            re.DOTALL | re.MULTILINE | re.UNICODE | re.IGNORECASE,
        )

    book_select_by = (By.XPATH, "/html/body/table[4]/tbody/tr/td/div[3]/table[2]/tbody/tr/td/form/div/table/tbody/tr[2]/td[2]/table/tbody/tr/td/select")
    keyword_by = (By.ID, "procura")
    calendar_start_by = (By.ID, "trigger2")
    calendar_end_by = (By.ID, "trigger3")
    search_by = (By.XPATH, '//*[@id="avancado"]/tbody/tr[5]/td[2]/table/tbody/tr/td/input[1]')
    results_by = (By.ID, 'divResultadosInferior')

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

    def find_cases_by_keyword(self, pdf_text, keyword_regex):
        if not keyword_regex:
            raise Exception("Missing arg keywords regex")

        cases_matched = []
        pdf_text = remove_accents(pdf_text)

        case_blocks = self.case_blocks_regex.findall(pdf_text)
        for block in case_blocks:
            block_has_keyword = keyword_regex.search(block)
            if block_has_keyword:
                case_number_match = self.case_number_regex.search(block)
                if case_number_match:
                    cases_matched.append(case_number_match.group(0))

        return cases_matched

    def find_cases_by_page_url(self, pdf_url, keyword_regex):
        pdf_text = ''
        
        try:
            previous_page_url = get_previous_page_url(pdf_url)
            previous_page_text = fetch_pdf_text_from_url(previous_page_url)
            actual_page_text = fetch_pdf_text_from_url(pdf_url)
            
            pdf_text = previous_page_text + actual_page_text

            cases = self.find_cases_by_keyword(pdf_text, keyword_regex)

            return cases
        
        except Exception as e:
            logger.error(f'Erro ao obter os processos da url: {pdf_url}', e)


class OccurrencesList(BaseComponent):
    def __init__(self, root):
        super().__init__(root)

    occurrences_by = (By.CLASS_NAME, 'fundocinza1')
    nav_buttons_by = (By.CSS_SELECTOR, 'span.style5 a')

    def get_occurences(self):
        occurrences = self.root.find_elements(*self.occurrences_by)
        return [Occurrence(item) for item in occurrences]
    
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
        anchor = self.root.find_elements(By.TAG_NAME, 'a')[0]
        regex = r"\('(.*?)'\)"
        endpoint = re.findall(regex, anchor.get_attribute('onclick'))[0]

        return TJ_BASE_URL + endpoint.replace(
            "consultaSimples", "getPaginaDoDiario"
        )


def get_previous_page_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if "nuSeqpagina" in query_params:
        current_nuSeqpagina = int(query_params["nuSeqpagina"][0])
        new_nuSeqpagina = current_nuSeqpagina - 1

        query_params["nuSeqpagina"] = [str(new_nuSeqpagina)]

        updated_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=updated_query))

        return new_url

    else:
        return url
