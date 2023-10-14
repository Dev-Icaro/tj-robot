from web_scraping.tj_scraping import TjWebScraping
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import sys, os
from common.utils.logger import logger
from common.utils.config_file import read_config_file, validate_config_params
from common.utils.xls import generate_xls_name, write_xls
from tests.test import test_specific_url, test_filter_result

def main():
    logger.info("Bem-vindo ao TJ Scraping!")

    try:
        config = read_config_file()
        validate_config_params(config)

    except Exception as e:
        logger.error(e)
        sys.exit()

    start_date = config["data_inicial_pesquisa"]
    end_date = config["data_final_pesquisa"]
    keywords = config["palavras_pesquisa"]
    book_option_text = config["caderno_pesquisa"]
    max_threads = config["maximo_requisicoes_simultaneas"]

    logger.info(
        (f"Iniciando 1° etapa: Pesquisa dos processos no Diário...\n\nCaderno: {book_option_text}\nPalavras-chave: {keywords}\nData Inicial: {start_date}\nData Final: {end_date}\n\n")
    )

    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument("--disable-logging")
    browser_options.add_argument("--log-level=3")

    browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=browser_options)
    scraping = TjWebScraping(browser)

    case_numbers = scraping.get_book_cases_by_keywords(
        book_option_text, keywords, start_date, end_date, max_threads
    )

    logger.info(f'Foram encontrados {len(case_numbers)} processos na pesquisa.')

    xls_dir = 'xls'
    xls_name = generate_xls_name()
    if not os.path.exists(xls_dir):
        os.mkdir(xls_dir)

    xls_object = { 'Processos analisados': case_numbers }

    xls_path = os.path.join(xls_dir, xls_name)
    write_xls(xls_path, xls_object)

    logger.info(
        f"Iniciando 2° etapa: Filtragem dos processos encontrados no Diário..."
    )

    wanted_exectdos = config['requeridos_filtro']
    filter_result = scraping.filter_cases_performing_search(case_numbers, wanted_exectdos)

    xls_object = { 'Processos analisados': case_numbers,
                   'Processos selecionados': filter_result }

    write_xls(xls_path, xls_object)

    logger.info(f'Resultado da pesquisa salvo no arquivo: {xls_path}\n\n Finalizando...')


if __name__ == "__main__":
    main()
    #test_specific_url()
    #test_scraping_result()
    #test_filter_result()
