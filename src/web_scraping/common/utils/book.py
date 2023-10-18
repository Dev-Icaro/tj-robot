from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from common.utils.pdf import fetch_pdf_text_from_url

class BookPage:
    def __init__(self, page_url, text):
        self.url = page_url
        self.text = text
        self.number = self.extract_page_number(page_url)

    def extract_page_number(self, page_url):
        parsed_url = urlparse(page_url)
        query_params = parse_qs(parsed_url.query)
        return int(query_params['nuSeqpagina'][0])


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
    

def separate_in_sequencial_chunks(pages):
    ordered_pages = sorted(pages, key=lambda obj: obj.number) 

    result = []
    chunk = [ordered_pages[0]]
    for i in range(1, len(ordered_pages)):
        cur_page = ordered_pages[i]
        prev_page = ordered_pages[i - 1]

        if cur_page.number - 1 == prev_page.number:
            chunk.append(cur_page)
        else:
            result.append(chunk)
            chunk = [cur_page]
    
    result.append(chunk)

    return result

        
        

    