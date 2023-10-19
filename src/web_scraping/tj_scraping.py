from time import sleep
import concurrent.futures
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from common.utils.array import remove_duplicate, flatten
from common.utils.string import remove_accents
from common.utils.logger import logger
from common.constants.tj_site import BASE_URL
from web_scraping.pages.book_search_page import BookSearchPage
from web_scraping.pages.case_page import CasePage
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

    def filter_cases_performing_search(self, cases, wanted_exectdos):
        filtered_cases = []

        wanted_exectdos = [
            remove_accents(exectdo).upper() for exectdo in wanted_exectdos
        ]

        cur_case_num = 0
        case_count = len(cases)
        for case_number in cases:
            try:
                case_page = self._load_case_page(case_number)
                cur_case_num += 1
                logger.info(f"Análisando processo {cur_case_num} de {case_count}")

                if case_page.is_private():
                    continue

                exectdo_name = case_page.get_exectdo_name()
                if exectdo_name not in wanted_exectdos:
                    continue

                filtered_cases.append(case_number)

                # try:
                #     judgment_execution = case_page.get_judgment_execution()
                #     if 'Cumprimento de Sentença' in judgment_execution:
                #         filtered_cases.append(case_number)
                # except:
                #     case_class = case_page.get_class()
                #     if 'Fazenda' in case_class:
                #         filtered_cases.append(case_number)

                # 1
                # if not case_page.has_incident():
                #     continue

            finally:
                self.driver.delete_all_cookies()
                # sleep(2)

        return filtered_cases

    def login(self, credentials):
        login_url = (
            BASE_URL
            + "/sajcas/login?service=https%3A%2F%2Fesaj.tjsp.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        )
        self.driver.get(login_url)

        input_cnpj = self.wait.until(
            EC.element_to_be_clickable((By.ID, "usernameForm"))
        )
        input_cnpj.send_keys(credentials.cnpj)

        input_pass = self.wait.until(
            EC.element_to_be_clickable((By.ID, "passwordForm"))
        )
        input_pass.send_keys(credentials.password)

        btn_login = self.wait.until(EC.element_to_be_clickable((By.ID, "pbEntrar")))
        btn_login.click()

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

    def _load_case_page(self, case_number):
        case_url = BASE_URL + "/cpopg/show.do?processo.numero=" + case_number
        self.driver.get(case_url)
        return CasePage(self.driver)


def clear_book_cases_result(cases):
    logger.info("Eliminando processos duplicados ...\n")
    return remove_duplicate(flatten(cases))
