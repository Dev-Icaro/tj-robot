import os
from selenium import webdriver
import time, sys
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from web_scraping.pages.book_search_page import BookSearchPage
from web_scraping.tj_scraping import TjWebScraping, clear_book_cases_result
from common.utils.logger import logger
from common.utils.config_file import read_config_file, validate_config_params
from common.utils.xls import generate_xls_name, write_xls
from common.utils.selenium import init_driver
from web_scraping.common.utils.book_page import separate_pages_in_sequencial_chunks


def test_scraping_result():
    logger.info("Bem-vindo ao TJ Scraping!")

    start_date = "19/09/2023"
    end_date = "19/09/2023"
    keywords = ["teste"]
    # book_option_text = "caderno 3 - Judicial - 1ª Instância - Capital"
    book_option_text = "caderno 3 - "
    max_threads = 10

    browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    scraping = TjWebScraping(browser)

    case_numbers = scraping.get_book_cases_by_keywords(
        book_option_text, keywords, start_date, end_date, max_threads
    )

    expected_result = [
        "0161645-79.2010.8.26.0100",
        "0003650-42.2013.8.26.0053",
        "1527760-59.2021.8.26.0050",
        "1008667-46.2023.8.26.0003",
        "1110470-82.2017.8.26.0100",
        "1523351-69.2023.8.26.0050",
        "1534456-43.2023.8.26.0050",
        "1012005-19.2016.8.26.0053",
        "1500747-52.2023.8.26.0006",
        "1006260-14.2023.8.26.0053",
        "1525024-97.2023.8.26.0050",
        "1056115-49.2022.8.26.0100",
        "1019609-65.2015.8.26.0053",
        "1120159-82.2019.8.26.0100",
        "1501118-84.2021.8.26.0006",
        "1001047-08.2015.8.26.0053",
        "1522941-59.2023.8.26.0228",
        "0195318-63.2010.8.26.0100",
        "1039018-46.2023.8.26.0053",
        "1500953-39.2023.8.26.0015",
        "1033333-04.2022.8.26.0050",
        "1537307-94.2019.8.26.0050",
        "1047135-79.2023.8.26.0100",
        "1036473-81.2015.8.26.0053",
        "1517997-14.2023.8.26.0228",
        "1060687-58.2023.8.26.0053",
        "0018785-94.2013.8.26.0053",
        "1501373-71.2023.8.26.0006",
        "0158795-52.2010.8.26.0100",
        "1029099-23.2022.8.26.0100",
        "1022782-19.2023.8.26.0053",
        "1004240-03.2023.8.26.0004",
        "1525477-43.2023.8.26.0228",
        "1043096-83.2023.8.26.0053",
        "1011695-13.2016.8.26.0053",
        "1109969-21.2023.8.26.0100",
        "1041584-65.2023.8.26.0053",
        "1500756-84.2023.8.26.0015",
        "1012056-12.2018.8.26.0004",
        "1055659-68.2023.8.26.0002",
        "1010155-27.2016.8.26.0053",
        "0006941-70.2022.8.26.0009",
        "1522179-43.2023.8.26.0228",
        "1521427-71.2023.8.26.0228",
        "0002696-54.2017.8.26.0635",
        "1014319-15.2021.8.26.0003",
        "1524502-21.2023.8.26.0228",
        "1011668-30.2016.8.26.0053",
        "0061758-98.2012.8.26.0053",
        "1021139-25.2023.8.26.0021",
        "1108240-57.2023.8.26.0100",
    ]

    if case_numbers == expected_result:
        print("Passed")
    else:
        print("Arrays should be equal")


def test_filter_result():
    requeridos = ["Banco do Brasil S/A", "Fazenda Pública do Estado de São Paulo"]

    # df = pd.read_excel("processos_analisados.xlsx")
    # found_cases = df["Processos analisados"].to_list()
    found_cases = ["0019690-51.2003.8.26.0053"]

    driver = init_driver()
    scraping = TjWebScraping(driver)

    scraping.login("28992745893", "Alice17*")
    filter_result = scraping.find_interesting_cases(found_cases, requeridos)

    xls_object = {
        "Processos analisados": found_cases,
        "Processos selecionados": filter_result,
    }

    xls_dir = "xls"
    xls_name = generate_xls_name()
    if not os.path.exists(xls_dir):
        os.mkdir(xls_dir)

    xls_path = os.path.join(xls_dir, xls_name)
    write_xls(xls_path, xls_object)

    logger.info(
        f"Resultado da pesquisa salvo no arquivo: {xls_path}\n\n Finalizando..."
    )


def test_specific_url():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    searcher = BookSearchPage(driver)

    url = "https://dje.tjsp.jus.br/cdje/getPaginaDoDiario.do?cdVolume=17&nuDiario=3823&cdCaderno=13&nuSeqpagina=1753"
    regex = searcher.prepare_keyword_regex(["Oficio Requisitorio"])
    cases = searcher.find_cases_by_page_url(url, regex)

    print(cases)


class TestObj:
    def __init__(self, number):
        self.number = number


def test_separation():
    data = [
        TestObj(1),
        TestObj(2),
        TestObj(4),
        TestObj(5),
        TestObj(7),
    ]

    res = separate_pages_in_sequencial_chunks(data)
    print(res)
