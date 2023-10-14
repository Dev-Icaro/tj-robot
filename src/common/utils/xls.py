import os
import pandas as pd
from datetime import datetime

def write_xls(file_path, data_frame):
    df = pd.DataFrame(data_frame)
    df.to_excel(file_path, engine="openpyxl", index=False)
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
    return f"pesquisa_{cur_datetime.strftime('%d/%m/%Y-%H:%M:%S')}.xlsx"