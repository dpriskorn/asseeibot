from pydantic.dataclasses import dataclass

from asseeibot.models.identifiers.identifier import Identifier

# How do we handle both 10 and 13?
from asseeibot.models.identifiers.isbn_enum import IsbnLength


@dataclass
class Isbn(Identifier):
    """Models an ISBN number"""
    isbn_length: IsbnLength = None
