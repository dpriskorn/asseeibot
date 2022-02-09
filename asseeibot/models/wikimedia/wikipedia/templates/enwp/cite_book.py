from typing import Optional

from asseeibot.models.identifier.isbn import Isbn
from asseeibot.models.wikimedia.wikipedia.templates.wikipedia_page_reference import WikipediaPageReference


class CiteBook(WikipediaPageReference):
    """This models the template cite book in English Wikipedia"""
    publisher: Optional[str] = None
    isbn: Optional[Isbn]

    def __post_init_post_parse__(self):
        pass
