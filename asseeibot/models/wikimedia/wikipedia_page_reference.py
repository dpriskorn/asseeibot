from pydantic import BaseModel


class WikipediaPageReference(BaseModel):
    """This models a reference on a Wikipedia page"""
    title: str = None
