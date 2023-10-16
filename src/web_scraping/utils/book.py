from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from common.utils.pdf import fetch_pdf_text_from_url

class Book:
    def __init__(self):
        self.pages = []

    def get_page_by_url(self, page_url):
        for page in self.pages:
            if page.url == page_url:
                return page

    def add_page(self, page):
        self.pages.append(page)

    def download_page(self, page_url):
        if self.has_page(page_url):
            return

        page_text = fetch_pdf_text_from_url(page_url)
        page = BookPage(page_url, page_text)
        self.add_page(page)

    def has_page(self, page_url):
        return True if self.get_page_by_url(page_url) else False

class BookPage:
    def __init__(self, page_url, text):
        self.url = page_url
        self.text = text

def get_previous_page_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if "nuSeqpagina" in query_params:
        current_nuSeqpagina = int(query_params["nuSeqpagina"][0])
        new_nuSeqpagina = current_nuSeqpagina - 1

        query_params["nuSeqpagina"] = [str(new_nuSeqpagina)]

        updated_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=updated_query))

        return new_url

    else:
        return url

    