import pandas as pd
import numpy as np
from datetime import datetime


def write_xls(file_path, data_frame):
    pd.set_option("display.max_colwidth", -1)
    df = pd.DataFrame.from_dict(data_frame, orient="index")
    df = df.transpose()
    df.to_excel(file_path, engine="openpyxl", index=False, na_rep="")
    # else:
    #     df_existing = pd.read_excel(
    #         file_path,
    #         engine="openpyxl",
    #         converters={col: str for col in df.columns},
    #     )
    #     df = pd.concat([df_existing, df], ignore_index=True)
    #     df.to_excel(file_path, engine="openpyxl", index=False)


def generate_xls_name():
    cur_datetime = datetime.now()
    return f"pesquisa_{cur_datetime.strftime('%d-%m-%Y_%H-%M-%S')}.xlsx"


def hyperlink_format(line):
    return "color: blue; text-decoration: underline"


def add_hyperlinks(row, urls, row_label):
    index = row.name
    label = row[row_label]
    if label:
        url = urls[index]
        return f'=HYPERLINK("{url}", "{label}")'
