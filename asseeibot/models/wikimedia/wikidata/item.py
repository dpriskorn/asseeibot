from urllib.parse import quote

from pydantic import BaseModel
from wikibaseintegrator.wbi_helpers import search_entities


class Item(BaseModel):

    @staticmethod
    def __call_wbi_search_entities__(subject):
        return search_entities(search_string=subject,
                               language="en",
                               dict_result=True,
                               max_results=1)

    @staticmethod
    def string_search_url(string: str) -> str:
        if string is not None and string != "":
            # quote to guard against äöå and the like
            return (
                    "https://www.wikidata.org/w/index.php?" +
                    "search={}&title=Special%3ASearch&".format(quote(string)) +
                    "profile=advanced&fulltext=0&" +
                    "advancedSearch-current=%7B%7D&ns0=1"
            )
