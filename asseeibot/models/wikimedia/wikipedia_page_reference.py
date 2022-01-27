from asseeibot.models.identifiers.doi import Doi
from asseeibot.models.identifiers.isbn import Isbn


class WikipediaPageReference:
    """This models a reference on a Wikipedia page"""
    doi: Doi = None
    isbn: Isbn = None
