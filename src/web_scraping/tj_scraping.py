from time import sleep
import concurrent.futures
from common.utils.array import remove_duplicate
from common.utils.string import upper_no_accent
from common.utils.logger import logger
from common.constants.tj_site import LOGIN_URL
from web_scraping.common.utils.tj import load_case_page, clear_book_cases_result
from web_scraping.common.utils.calendar import calc_valid_calendar_date
from web_scraping.common.exceptions import (
    DisabledCalendarDateException,
    InvalidPageException,
)
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
        self.number = case_number
        self.url = case_url


class CasesResult:
    def __init__(self):
        self.precatorys = []
        self.judgment_executions = []

    def add_precatory_url(self, case_url):
        if not case_url in self.precatorys:
            self.precatorys.append(case_url)

    def add_judgment_execution(self, case):
        executions_cases = self.get_judgment_executions()
        for execution in executions_cases:
            if execution.url == case.url:
                return

        self.judgment_executions.append(case)

    def get_precatory_urls(self):
        return self.precatorys

    def get_judgment_executions(self):
        return self.judgment_executions


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

    def get_interesting_cases_incidents(self, cases, respondents):
        incidents = CasesResult()
        respondents = [upper_no_accent(respondent) for respondent in respondents]

        i = 0
        for case_number in cases:
            try:
                i += 1
                logger.info(f"Analisando processo {i} de {len(cases)} ...")

                case = load_case_page(self.driver, case_number)

                if case.is_private():
                    continue

                if case.has_main_case():
                    case.navigate_to_main_case()

                case_respondent = case.get_respondent()
                if case_respondent not in respondents:
                    continue

                incidents = self.get_interesting_incidents(case, incidents)

            except InvalidPageException:
                continue

            finally:
                self.driver.delete_all_cookies()
                sleep(0.2)

        count_precatorys = len(incidents.get_precatory_urls())
        count_judgments_exec = len(incidents.get_judgment_executions())
        logger.info(
            f"\nForam encontrados {count_precatorys} Precatórios e {count_judgments_exec} Cumprimentos sem incidentes.\n"
        )

        return incidents

    def get_interesting_incidents(self, case_page: CasePage, result: CasesResult):
        if case_page.is_private():
            return result

        if case_page.has_incident():
            incidents = case_page.get_incidents()
            for incident in incidents:
                if incident.is_judgment_execution():
                    try:
                        incident_url = incident.get_case_url()
                        self.driver.get(incident_url)
                        self.get_interesting_incidents(CasePage(self.driver), result)
                    except InvalidPageException:
                        continue

                elif incident.is_precatory():
                    incident_url = incident.get_case_url()
                    result.add_precatory_url(incident_url)
                else:
                    continue
        else:
            if case_page.is_judgment_execution():
                case_number = IncidentCasePage(self.driver).get_case_number()
                judgment_execution = Case(case_number, self.driver.current_url)
                result.add_judgment_execution(judgment_execution)

        return result

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
                    f"Efetuando download das páginas do diário {cur_page} de {page_count} ..."
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
                sleep(0.35)
            else:
                finished = True

        return pdf_urls

    def _init_search_page(self, book_option_text, keywords, start_date, end_date):
        search_page = BookSearchPage(self.driver)
        search_page.select_book(book_option_text).set_keyword(keywords)
        try:
            search_page.set_start_date(start_date)
        except DisabledCalendarDateException:
            search_page.set_start_date(calc_valid_calendar_date(start_date))

        try:
            search_page.set_end_date(end_date)
        except DisabledCalendarDateException:
            search_page.set_end_date(calc_valid_calendar_date(end_date))

        return search_page

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
