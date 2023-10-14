from datetime import datetime, timedelta
from common.utils.string import remove_accents
from common.utils.pdf import fetch_pdf_text_from_url
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from common.utils.logger import logger
from common.exceptions.app_exception import AppException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from web_scraping.components.calendar import find_calendar
from web_scraping.pages.base_page import BasePage

import re

PDF_ELEMENT_XPATH = "/html/body/embed"
PAGES_RESULT_ELEMENT_XPATH = '//*[@id="divResultadosSuperior"]/table/tbody/tr[1]/td[1]'

class BookSearchPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        if not 'Consulta de Diário da Justiça Eletrônico' in self.driver.title:
            raise AppException('Pagina atual não é a página de consulta do diário', 
                               'URL atual: ' + self.driver.get_current_url())
        
        self.select_by = (By.XPATH, "/html/body/table[4]/tbody/tr/td/div[3]/table[2]/tbody/tr/td/form/div/table/tbody/tr[2]/td[2]/table/tbody/tr/td/select")
        self.keyword_by = (By.ID, "procura")
        self.calendar_start_by = (By.ID, "trigger2")
        self.calendar_end_by = (By.ID, "trigger3")
        self.search_by = (By.XPATH, '//*[@id="avancado"]/tbody/tr[5]/td[2]/table/tbody/tr/td/input[1]')

        self.case_number_regex = re.compile(
            r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2,4}\.\d{4}"
        )

        self.case_blocks_regex = re.compile(
            r"(?:\n+Processo\s+\d+|^Processo\s+\d+|\n+No\s+\d+|^No\s+\d+)[\s\S]*?(?=\-\s+ADV|\Z)",
            re.DOTALL | re.MULTILINE | re.UNICODE | re.IGNORECASE,
        )

    def select_book(self, option_text):
        select = Select(self.driver.find_element(*self.select_by))
        options_text = [option.text for option in select.options]

        if option_text in options_text:
            select.select_by_visible_text(option_text)
        else:
            raise AppException(
                "O Caderno definido para a pesquisa não foi encontrado, por favor selecionar uma opção valida"
            )
        
    def set_keyword(self, keywords):
        keywords = " OU ".join(keywords)
        self.driver.find_element(*self.keyword_by).send_keys(keywords)

    def set_start_date(self, date):
        self.driver.find_element(*self.calendar_start_by).click()
        calendar = find_calendar(self.driver)
        calendar.set_date(date)

    def set_end_date(self, date):
        self.driver.find_element(*self.calendar_end_by).click()
        calendar = find_calendar(self.driver)
        calendar.set_date(date)

    def click_search_button(self):
        self.driver.find_element(*self.search_by).click()

    def prepare_keyword_regex(self, keywords):
        for i in range(len(keywords)):
            keyword = keywords[i]

            while keyword.find(" ") != -1:
                keyword = keyword.replace(" ", r"\s+")
                
            keyword = remove_accents(keyword).lower()
            keywords[i] = keyword

        union_keyword = "|".join(keywords)
        return re.compile(
            union_keyword,
            re.IGNORECASE | re.UNICODE | re.MULTILINE | re.DOTALL,
        )

    def extract_pdf_urls_from_results(self):
        pdf_urls = []
        base_url = "https://esaj.tjsp.jus.br"

        self.driver.implicitly_wait(1)

        occurrence_elements = self.wait.until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, "tr.ementaclass a:first-child")
            )
        )

        link_regex = re.compile(r"\('(.*?)'\)")
        for ocurrence in occurrence_elements:
            endpoint = link_regex.findall(ocurrence.get_attribute("onclick"))[0]
            pdf_url = base_url + endpoint.replace(
                "consultaSimples", "getPaginaDoDiario"
            )
            pdf_urls.append(pdf_url)

        return pdf_urls

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

    def find_next_button(self):
        button_span = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.style5"))
        )
        a_elements = button_span.find_elements(By.TAG_NAME, "a")

        for a in a_elements:
            if a.text == "Próximo>":
                return a

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


def extract_pdf_link(occurrence_element):
    re_pattern = r"\('(.*?)'\)"
    return re.findall(re_pattern, occurrence_element.get_attribute("onclick"))[0]


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
