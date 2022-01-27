from asseeibot.models.identifier import Identifier

# How do we handle both 10 and 13?
from asseeibot.models.isbn_enum import IsbnLength


class Isbn(Identifier):
    """Models an ISBN number"""
    isbn_length: IsbnLength = None

    # todo test it with a regex on init and detect length