from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import re
from common.utils.string import remove_accents

class BookPage:
    def __init__(self, page_url, text):
        self.url = page_url
        self.text = text
        self.number = self.extract_page_number(page_url)

    def extract_page_number(self, page_url):
        parsed_url = urlparse(page_url)
        query_params = parse_qs(parsed_url.query)
        return int(query_params['nuSeqpagina'][0])


class CaseNumberExtractor:
    def __init__(self, keywords):
        self.case_number_regex = re.compile(
            r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2,4}\.\d{4}"
        )

        self.case_blocks_regex = re.compile(
            r"(?:\n+Processo\s+\d+|^Processo\s+\d+|\n+No\s+\d+|^No\s+\d+)[\s\S]*?(?=\-\s+ADV|\Z)",
            re.DOTALL | re.MULTILINE | re.UNICODE | re.IGNORECASE,
        )

        self.keyword_regex = self._prepare_keyword_regex(keywords)

    def _prepare_keyword_regex(keywords):
        for i in range(len(keywords)):
            keyword = keywords[i]

            while keyword.find(" ") != -1:
                keyword = keyword.replace(" ", r"\s+")
                
            keyword = remove_accents(keyword).lower()
            keywords[i] = keyword

        union_keyword = "|".join(keywords)
        return re.compile(
            union_keyword,
            re.IGNORECASE | re.UNICODE | re.MULTILINE | re.DOTALL,
        )

    def find_cases_by_keyword(self, pdf_text):
        if not self.keyword_regex:
            raise Exception("Missing arg keywords regex")

        cases_matched = []
        pdf_text = remove_accents(pdf_text)

        case_blocks = self.case_blocks_regex.findall(pdf_text)
        for block in case_blocks:
            block_has_keyword = self.keyword_regex.search(block)
            if block_has_keyword:
                case_number_match = self.case_number_regex.search(block)
                if case_number_match:
                    cases_matched.append(case_number_match.group(0))

        return cases_matched
        

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
    
def separate_pages_in_sequencial_chunks(pages):
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



        
        

    