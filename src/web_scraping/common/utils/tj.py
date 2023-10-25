from common.constants.tj_site import CASE_SEARCH_URL
from common.utils.logger import logger
from common.utils.array import remove_duplicate, flatten
from common.utils.xls import generate_xls_name, hyperlink_format, add_hyperlinks
from web_scraping.pages.case_search_page import CaseSearchPage
import os
import pandas as pd


def load_case_page(driver, case_number):
    driver.get(CASE_SEARCH_URL)
    search_page = CaseSearchPage(driver)
    return search_page.search_case(case_number)


def save_result_to_xls_folder(analyzed_cases, precatorys, enforcement_judgments):
    xls_dir = "xls"
    xls_name = generate_xls_name()
    xls_path = os.path.join(xls_dir, xls_name)

    if not os.path.exists(xls_dir):
        os.mkdir(xls_dir)

    xls_object = {
        "Processos analisados": analyzed_cases,
        "Precatórios": [precatory.number for precatory in precatorys],
        "Cumprimentos sem incidentes": [
            enforcement_judgment.number
            for enforcement_judgment in enforcement_judgments
        ],
    }

    df = pd.DataFrame.from_dict(xls_object, orient="index")
    df = df.transpose()

    column = "Precatórios"
    precatory_urls = [precatory.url for precatory in precatorys]
    df[column] = df.apply(add_hyperlinks, urls=precatory_urls, row_label=column, axis=1)

    column = "Cumprimentos sem incidentes"
    enforcement_urls = [enforcement.url for enforcement in enforcement_judgments]
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
