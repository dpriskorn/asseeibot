from typing import Optional, Union

from pydantic import BaseModel, PositiveInt, conint

from asseeibot.models.crossref_engine.enums import CrossrefContentType


class CrossrefLink(BaseModel):
    url: str
    content_type: Optional[CrossrefContentType]
    intended_application: Optional[str]


class CrossrefReference(BaseModel):
    key: Optional[str]
    # doi-asserted-by
    first_page: Optional[Union[PositiveInt, str]]
    doi: Optional[str]
    article_title: Optional[str]
    volume: Optional[str]  # This is often a PositiveInt but str like "Volume 8" do appear
    author: Optional[str]
    year: Optional[Union[conint(gt=1800, lt=2023), str]]  # can be a string like "2002a"
    journal_tile: Optional[str]
