from urllib.parse import quote

from pydantic import BaseModel


class Item(BaseModel):

    def string_search_url(string: str) -> str:
        if string is not None and string != "":
            # quote to guard against äöå and the like
            return (
                    "https://www.wikidata.org/w/index.php?" +
                    "search={}&title=Special%3ASearch&".format(quote(string)) +
                    "profile=advanced&fulltext=0&" +
                    "advancedSearch-current=%7B%7D&ns0=1"
            )
