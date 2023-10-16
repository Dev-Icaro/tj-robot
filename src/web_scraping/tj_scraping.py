from time import sleep
import concurrent.futures
import re
from common.utils.array import remove_duplicate, flatten
from common.utils.string import remove_accents
from common.utils.logger import logger
from web_scraping.pages.book_search_page import BookSearchPage
from web_scraping.pages.tj_case_searcher import TjCaseSearcher
from web_scraping.utils.book import Book, get_previous_page_url


TJ_SITE_URL = "https://www.tjsp.jus.br/"


class TjWebScraping:
    def __init__(self, driver):
        self.driver = driver

    def navigate_to_tj_site(self):
        self.driver.get(TJ_SITE_URL)

    def get_book_cases_by_keywords(
        self, book_option_text, keywords, start_date, end_date, max_threads=4
    ):
        found_cases = []
        search_page = BookSearchPage(self.driver)

        search_page \
            .select_book(book_option_text) \
            .set_keyword(keywords) \
            .set_start_date(start_date) \
            .set_end_date(end_date)
            
        occurrences_list = search_page.click_search_button()
        pdf_urls = [occurrence.get_pdf_url() for occurrence in occurrences_list.get_occurences()]
        while occurrences_list.has_next_page():
            occurrences_list.next_page()
            sleep(1)
            pdf_urls += [occurrence.get_pdf_url() for occurrence in occurrences_list.get_occurences()]

        pdf_urls = add_previous_pages_urls(pdf_urls)
        book = Book()
        for url in pdf_urls:
            book.download_page(url)

        keyword_regex = prepare_keyword_regex(keywords)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_threads
        ) as executor:
            
            results = list(
                executor.map(
                    lambda args: search_page.find_cases_by_page_url
                    (
                        args, 
                        keyword_regex
                    ),
                    pdf_urls,
                )
            )

        case_count = 0
        for result in results:
            case_count += len(result)
            found_cases.append(result)

        #logger.info(f'Foram encontrados {case_count} processos na página {page_count} de resultados do Diário')
        return clear_book_cases_result(found_cases)

    def filter_cases_performing_search(self, cases, wanted_exectdos):
        case_searcher = TjCaseSearcher(self.driver)
        filtered_cases = []

        wanted_exectdos = [remove_accents(exectdo).upper() for exectdo in wanted_exectdos]

        #case_searcher.login(credentials)

        cur_case_num = 0
        case_count = len(cases)
        for case_number in cases:
            try:
                cur_case_num += 1
                logger.info(f'Análisando processo {cur_case_num} de {case_count}')
                
                case_page = case_searcher.load_case_page(case_number)

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
                #sleep(2)

        return filtered_cases


def clear_book_cases_result(cases):
    logger.info('\n\nEliminando processos duplicados ...\n\n')
    return remove_duplicate(flatten(cases))


def prepare_keyword_regex(keywords):
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

def add_previous_pages_urls(pages_urls):
    new_pages_list = []

    for url in pages_urls:
        new_pages_list.append(url)
        new_pages_list.append(get_previous_page_url(url))

    return remove_duplicate(new_pages_list)



    
