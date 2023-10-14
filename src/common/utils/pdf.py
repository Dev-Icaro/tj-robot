import requests, io
from pdfminer.high_level import extract_text


def fetch_pdf_text_from_url(pdf_url):
    pdf_text = ""

    response = requests.get(pdf_url)
    if response.status_code == 200:
        pdf_file = io.BytesIO(response.content)
        pdf_text = extract_text(pdf_file)

        return pdf_text
    else:
        raise Exception("Falha ao obter a página do pdf, possivel erro de internet")
