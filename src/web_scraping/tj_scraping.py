from datetime import timedelta, datetime
import os, xlsxwriter
from time import sleep
import concurrent.futures
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from common.utils.array import remove_duplicate, flatten
from common.utils.string import remove_accents, upper_no_accent
from common.utils.logger import logger
from common.constants.tj_site import CASE_SEARCH_URL, LOGIN_URL
from common.utils.xls import generate_xls_name, add_hyperlinks, hyperlink_format
from common.exceptions.app_exception import AppException, RequiredArgumentException
from web_scraping.common.exceptions import (
    DisabledCalendarDateException,
    InvalidPageException,
)
from web_scraping.pages.case_search_page import CaseSearchPage
from web_scraping.pages.book_search_page import BookSearchPage
from web_scraping.pages.case_page import CasePage
from web_scraping.pages.incident_case_page import IncidentCasePage
from web_scraping.pages.login_page import LoginPage
from web_scraping.common.utils.book_page import (
    CaseNumberExtractor,
    get_previous_page_url,
    separate_pages_in_sequencial_chunks,
    fetch_page_from_url,
)


class Case:
    def __init__(self, case_number, case_url):
        self.case_number = case_number
        self.case_url = case_url


class CasesResult:
    def __init__(self):
        self.precatorys = []
        self.enforcement_judgment = []

    def add_precatory_url(self, case_url):
        if not case_url in self.precatorys:
            self.precatorys.append(case_url)

    def add_judgment_execution_url(self, case_url):
        if not case_url in self.enforcement_judgment:
            self.enforcement_judgment.append(case_url)

    def get_precatory_urls(self):
        return self.precatorys

    def get_judgment_execution_urls(self):
        return self.enforcement_judgment


class TjWebScraping:
    def __init__(self, driver):
        self.driver = driver

    def get_book_cases_by_keywords(
        self, book_option_text, keywords, start_date, end_date
    ):
        search_page = self._init_search_page(
            book_option_text, keywords, start_date, end_date
        )
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

    def find_interesting_cases(self, cases, wanted_exectdos):
        wanted_exectdos = [upper_no_accent(exectdo) for exectdo in wanted_exectdos]
        interesting_cases = CasesResult()
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

                interesting_cases = self.get_interesting_cases(
                    case_page, interesting_cases
                )

            except InvalidPageException:
                continue

            finally:
                self.driver.delete_all_cookies()
                sleep(0.3)

        count_precatorys = len(interesting_cases.get_precatory_urls())
        count_judgments_exec = len(interesting_cases.get_judgment_execution_urls())
        logger.info(
            f"\nForam encontrados {count_precatorys} Precatórios e {count_judgments_exec} Cumprimentos sem incidentes.\n"
        )

        return interesting_cases

    def get_interesting_cases(
        self, case_page: CasePage, interesting_cases: CasesResult
    ):
        if case_page.is_private():
            return interesting_cases

        if case_page.has_incident():
            incidents = case_page.get_incidents()
            for incident in incidents:
                if incident.is_judgment_execution():
                    incident_url = incident.get_case_url()
                    self.driver.get(incident_url)
                    self.get_interesting_cases(CasePage(self.driver), interesting_cases)
                elif incident.is_precatory():
                    interesting_cases.add_precatory_url(incident.get_case_url())
                else:
                    continue

        else:
            if case_page.is_judgment_execution():
                interesting_cases.add_judgment_execution_url(self.driver.current_url)

        sleep(0.3)
        return interesting_cases

    def load_case_page(self, case_number):
        self.driver.get(CASE_SEARCH_URL)
        search_page = CaseSearchPage(self.driver)
        return search_page.search_case(case_number)

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

    def _init_search_page(self, book_option_text, keywords, start_date, end_date):
        search_page = BookSearchPage(self.driver)
        search_page.select_book(book_option_text).set_keyword(keywords)
        try:
            search_page.set_start_date(start_date)
        except DisabledCalendarDateException:
            search_page.set_start_date(self.calc_valid_calendar_date(start_date))

        try:
            search_page.set_end_date(end_date)
        except DisabledCalendarDateException:
            search_page.set_end_date(self.calc_valid_calendar_date(end_date))

        return search_page

    def calc_valid_calendar_date(self, date):
        date = datetime.strptime(date, "%d/%m/%Y")

        if date.weekday() == 5:
            date = date - timedelta(1)
        elif date.weekday() == 6:
            date = date - timedelta(2)

        return date

    def filter_precatorys(self, precatory_urls):
        filtered_precatorys = []
        precatory_count = len(precatory_urls)
        cur_precatory = 0
        for url in precatory_urls:
            try:
                cur_precatory += 1
                logger.info(
                    f"Filtrando precatórios {cur_precatory} de {precatory_count} ... "
                )

                self.driver.get(url)
                case_page = IncidentCasePage(self.driver)

                precatory_situation = case_page.get_situation()
                if precatory_situation in ["EXTINTO", "ARQUIVADO"]:
                    continue

                precatory_number = case_page.get_case_number()
                precatory = Case(precatory_number, url)

                filtered_precatorys.append(precatory)
            finally:
                sleep(0.3)

        return filtered_precatorys

    def get_case_number_by_url(self, case_url):
        if not case_url:
            raise RequiredArgumentException(
                "URL do processo é um argumento obrigatório"
            )
        sleep(0.3)
        self.driver.get(case_url)
        case_page = IncidentCasePage(self.driver)
        return case_page.get_case_number()


def clear_book_cases_result(cases):
    logger.info("Eliminando processos duplicados ...")
    return remove_duplicate(flatten(cases))


def save_result_to_xls_folder(analyzed_cases, precatorys, enforcement_judgments):
    xls_dir = "xls"
    xls_name = generate_xls_name()
    xls_path = os.path.join(xls_dir, xls_name)

    if not os.path.exists(xls_dir):
        os.mkdir(xls_dir)

    xls_object = {
        "Processos analisados": analyzed_cases,
        "Precatórios": [precatory.case_number for precatory in precatorys],
        "Cumprimentos sem incidentes": [
            enforcement_judgment.case_number
            for enforcement_judgment in enforcement_judgments
        ],
    }

    df = pd.DataFrame.from_dict(xls_object, orient="index")
    df = df.transpose()

    column = "Precatórios"
    precatory_urls = [precatory.case_url for precatory in precatorys]
    df[column] = df.apply(add_hyperlinks, urls=precatory_urls, row_label=column, axis=1)

    column = "Cumprimentos sem incidentes"
    enforcement_urls = [enforcement.case_url for enforcement in enforcement_judgments]
    df[column] = df.apply(
        add_hyperlinks, urls=enforcement_urls, row_label=column, axis=1
    )

    styled_df = df.style.map(
        hyperlink_format, subset=["Precatórios", "Cumprimentos sem incidentes"]
    )

    writer = pd.ExcelWriter(xls_path)
    styled_df.to_excel(writer, sheet_name="Sheet1", index=False, na_rep="")

    for column in df:
        column_length = 30
        col_idx = df.columns.get_loc(column)
        writer.sheets["Sheet1"].set_column(col_idx, col_idx, column_length)

    writer.close()
    logger.info(f"\nResultado da pesquisa salvo no arquivo: '{xls_path}'")
