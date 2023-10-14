import json, os
from common.utils.date import is_valid_date, InvalidDateError
from common.utils.errors import format_error_message


ERROR_MISSING_CONFIG_PARAM = (
    'Está faltando o paramêtro "(0)" no arquivo de configuração.'
)
ERROR_MISSING_CONFIG_FILE = (
    "Arquivo de configuração não encontrado na pasta do projeto."
)
ERROR_INVALID_CONFIG_PARAM = 'Paramêtro "(0)" no arquivo de configuração inválido.'


def read_config_file():
    if not os.path.isfile("config.json"):
        raise FileNotFoundError(ERROR_MISSING_CONFIG_PARAM)

    with open("config.json", "r", -1, "utf8") as config_file:
        config = json.load(config_file)

    return config


def validate_config_params(config):
    start_date = config["data_inicial_pesquisa"]
    end_date = config["data_final_pesquisa"]
    keyword = config["palavras_pesquisa"]
    book_option_text = config["caderno_pesquisa"]
    exectdos = config['requeridos_filtro']

    if not is_valid_date(start_date):
        raise InvalidDateError(
            format_error_message(ERROR_INVALID_CONFIG_PARAM, [f"data_inicial_pesquisa"])
        )

    if not is_valid_date(end_date):
        raise InvalidDateError(
            format_error_message(ERROR_INVALID_CONFIG_PARAM, [f"data_final_pesquisa"])
        )

    if not keyword:
        raise Exception(format_error_message(ERROR_MISSING_CONFIG_PARAM, ["palavras_pesquisa"]))

    if not book_option_text:
        raise Exception(
            format_error_message(ERROR_MISSING_CONFIG_PARAM, ["caderno_pesquisa"])
        )
    
    if not exectdos: 
        raise Exception(
            format_error_message(ERROR_MISSING_CONFIG_PARAM, ["requeridos_filtro"])
        )