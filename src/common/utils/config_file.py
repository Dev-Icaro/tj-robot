import json
from common.utils.date import is_valid_date
from common.exceptions.app_exception import AppException


def read_config_file():
    try:
        with open("config.json", "r", -1, "utf8") as config_file:
            config = json.load(config_file)

        validate_config_params(config)
        return config
    except FileNotFoundError:
        raise AppException("O arquivo de configuração não foi encontrado")
    except json.JSONDecodeError as e:
        raise AppException(
            f"Formatação do arquivo de configuração está inválida: {str(e)}"
        )


def validate_config_params(config):
    start_date = config["data_inicial_pesquisa"]
    end_date = config["data_final_pesquisa"]
    keyword = config["palavras_pesquisa"]
    book_option_text = config["caderno_pesquisa"]
    exectdos = config["requeridos_filtro"]

    if not is_valid_date(start_date):
        raise AppException("Data inicial inválida")

    if not is_valid_date(end_date):
        raise AppException("Data final inválida")

    if not keyword:
        raise AppException("Palavras-chaves não informadas")

    if not book_option_text:
        raise AppException("Diário não informado")

    if not exectdos:
        raise AppException("Requeridos para filtragem de processos não informados")
