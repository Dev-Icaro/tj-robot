import os
from time import sleep
import concurrent.futures
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from common.utils.array import remove_duplicate, flatten
from common.utils.string import remove_accents
from common.utils.logger import logger
from common.constants.tj_site import BASE_URL, LOGIN_URL
from common.utils.xls import generate_xls_name, write_xls
from common.exceptions.app_exception import AppException
from web_scraping.common.exceptions.invalid_page_exception import (
    InvalidPageException,
)
from web_scraping.pages.case_search_page import CaseSearchPage
from web_scraping.pages.book_search_page import BookSearchPage
from web_scraping.pages.case_page import CasePage
from web_scraping.pages.login_page import LoginPage
from web_scraping.common.utils.book_page import (
    CaseNumberExtractor,
    get_previous_page_url,
    separate_pages_in_sequencial_chunks,
    fetch_page_from_url,
)


class TjWebScraping:
    def __init__(self, driver):
        self.driver = driver

    def get_book_cases_by_keywords(
        self, book_option_text, keywords, start_date, end_date
    ):
        search_page = BookSearchPage(self.driver)
        search_page.select_book(book_option_text).set_keyword(keywords).set_start_date(
            start_date
        ).set_end_date(end_date)

        occurrences_list = search_page.click_search_button()
        book_pages = self._get_occurrences_pages(occurrences_list)
        pages_chunks = separate_pages_in_sequencial_chunks(book_pages)

        logger.info("\nExtraindo números de processos das páginas ...")
        found_cases = []
        cases_extractor = CaseNumberExtractor(keywords)
        for chunk in pages_chunks:
            text = ""
            for page in chunk:
                text += page.text

            found_cases += cases_extractor.find_cases_by_keyword(text)

        return clear_book_cases_result(found_cases)

    def find_cases_precatorys(self, cases, wanted_exectdos):
        filtered_cases = []

        wanted_exectdos = [
            remove_accents(exectdo).upper() for exectdo in wanted_exectdos
        ]

        cur_case_num = 0
        case_count = len(cases)
        for case_number in cases:
            try:
                cur_case_num += 1
                logger.info(f"Análisando processo {cur_case_num} de {case_count} ...")

                case_page = self.load_case_page(case_number)

                if case_page.is_private():
                    continue

                if case_page.has_main_case():
                    case_page = case_page.navigate_to_main_case()

                exectdo_name = case_page.get_exectdo_name()
                if exectdo_name not in wanted_exectdos:
                    continue

                if not case_page.has_incident():
                    continue

                precatorys = self.get_precatorys(case_page, [])
                print(precatorys)

            except InvalidPageException:
                continue

            finally:
                self.driver.delete_all_cookies()
                sleep(0.3)

        return filtered_cases

    def get_precatorys(self, case_page: CasePage, precatorys):
        if not case_page.has_incident():
            return precatorys

        incidents = case_page.get_incidents()
        for incident in incidents:
            incident_class = incident.get_class()

            if "Cumprimento de Sentença" in incident_class:
                incident_case_link = incident.get_case_link()
                self.driver.get(incident_case_link)
                self.get_precatorys(CasePage(self.driver), precatorys)
            elif "Precatório" in incident_class:
                precatorys.append(incident.get_case_link())
            else:
                continue

        return precatorys

    def load_case_page(self, case_number):
        case_url = BASE_URL + "/cpopg/show.do?processo.numero=" + case_number
        self.driver.get(case_url)

        if not "processo.codigo" in self.driver.current_url:
            # Will enter in this block if get some error to get the case page by url
            # so we try another method.
            search_page = CaseSearchPage(self.driver)
            return search_page.search_case(case_number)
        else:
            return CasePage(self.driver)

    def login(self, username, password):
        self.driver.get(LOGIN_URL)
        login_page = LoginPage(self.driver)
        login_page.login_as(username, password)

    def _get_occurrences_pages(self, occurrences_list):
        pages = []

        pages_urls = self._extract_pages_urls(occurrences_list)
        prev_pages_urls = [get_previous_page_url(url) for url in pages_urls]
        pages_urls += prev_pages_urls
        pages_urls = remove_duplicate(pages_urls)

        logger.info(
            f"\nForam extraidos {len(pages_urls)} links de páginas, Iniciando Download.\n"
        )

        page_count = len(pages_urls)
        cur_page = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(fetch_page_from_url, url) for url in pages_urls]

            for future in concurrent.futures.as_completed(futures):
                cur_page += 1
                logger.info(
                    f"Efetuando download das páginas do diário ... {cur_page} de {page_count}"
                )
                page = future.result()
                pages.append(page)

        return pages

    def _extract_pages_urls(self, occurrences_list):
        pdf_urls = []
        finished = False
        while not finished:
            logger.info(
                f"Extraindo links das ocorrências da página: {occurrences_list.get_page_number()} ..."
            )
            pdf_urls += [
                occurrence.get_pdf_url()
                for occurrence in occurrences_list.get_occurences()
            ]

            if occurrences_list.has_next_page():
                occurrences_list.next_page()
                sleep(0.3)
            else:
                finished = True

        return pdf_urls


def clear_book_cases_result(cases):
    logger.info("Eliminando processos duplicados ...")
    return remove_duplicate(flatten(cases))


def save_result_to_xls_folder(analyzed_cases, filtered_cases):
    xls_dir = "xls"
    xls_name = generate_xls_name()
    xls_path = os.path.join(xls_dir, xls_name)

    if not os.path.exists(xls_dir):
        os.mkdir(xls_dir)

    while len(analyzed_cases) > len(filtered_cases):
        filtered_cases.append("")

    xls_object = {
        "Processos analisados": analyzed_cases,
        "Processos selecionados": filtered_cases,
    }

    write_xls(xls_path, xls_object)
    logger.info(
        f"Resultado da pesquisa salvo no arquivo: {xls_path}\n\n Finalizando..."
    )
