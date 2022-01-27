from typing import Optional

from pydantic import BaseModel

from asseeibot.models.identifiers.doi import Doi
from asseeibot.models.identifiers.isbn import Isbn


class WikipediaPageReference(BaseModel):
    """This models a reference on a Wikipedia page"""
    doi: Optional[Doi] = None
    isbn: Optional[Isbn] = None
