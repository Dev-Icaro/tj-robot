from web_scraping.tj_scraping import TjWebScraping, save_result_to_xls_folder
import sys
import os
from common.utils.logger import logger
from common.utils.selenium import init_driver
from common.utils.config_file import read_config_file
from tests.test import test_specific_url, test_filter_result, test_separation


def main():
    logger.info("Bem-vindo ao TJ Scraping!\n")

    try:
        config = read_config_file()
        start_date = config["data_inicial_pesquisa"]
        end_date = config["data_final_pesquisa"]
        keywords = config["palavras_pesquisa"]
        book_option_text = config["caderno_pesquisa"]

        logger.info(
            "Iniciando 1° etapa: Pesquisa dos processos no Diário...\n\n"
            f"Caderno: {book_option_text}\n"
            f"Palavras-chave: {keywords}\n"
            f"Data Inicial: {start_date}\n"
            f"Data Final: {end_date}"
        )

        driver = init_driver()
        scraping = TjWebScraping(driver)

        case_numbers = scraping.get_book_cases_by_keywords(
            book_option_text, keywords, start_date, end_date
        )

        logger.info(
            f"Foram encontrados {len(case_numbers)} processos na pesquisa.\n"
            f"Iniciando 2° etapa: Filtragem dos processos encontrados no Diário..."
        )

        wanted_exectdos = config["requeridos_filtro"]
        user = config["usuario_tj"]
        password = config["senha_tj"]

        scraping.login(user, password)
        filter_result = scraping.filter_cases_performing_search(
            case_numbers, wanted_exectdos
        )

        save_result_to_xls_folder(case_numbers, filter_result)

    except Exception as e:
        logger.error(e)
        sys.exit()

    finally:
        driver.quit()


if __name__ == "__main__":
    # main()
    # test_specific_url()
    # test_scraping_result()
    test_filter_result()
# test_separation()
