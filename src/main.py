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
            f"Iniciando 2° etapa: Extração dos precatórios dos processos encontrados..."
        )

        wanted_exectdos = config["requeridos_filtro"]
        user = config["usuario_tj"]
        password = config["senha_tj"]

        scraping.login(user, password)
        interesting_cases = scraping.find_interesting_cases(
            case_numbers, wanted_exectdos
        )

        precatorys = scraping.filter_precatorys(interesting_cases.get_precatory_urls())
        enforcement_judgment = interesting_cases.get_enforcement_judgment_urls()

        save_result_to_xls_folder(case_numbers, interesting_cases)

    except Exception as e:
        logger.error(e)

    finally:
        driver.quit()
        sys.exit("Finalizando ... Até mais!")


if __name__ == "__main__":
    # main()
    # test_specific_url()
    # test_scraping_result()
    test_filter_result()
    # test_separation()
