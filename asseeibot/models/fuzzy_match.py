from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel

from asseeibot.models.wikimedia.wikidata.entity import EntityId


class MatchBasedOn(Enum):
    LABEL = "label"
    ALIAS = "alias"


class FuzzyMatch(BaseModel):
    crossref_subject: Optional[str]
    qid: Optional[EntityId]
    edited_qid: Optional[EntityId]
    match_based_on: Optional[MatchBasedOn]
    original_subject: Optional[str]
    split_subject: Optional[bool]
    alias: Optional[str]
    label: Optional[str]
    description: Optional[str]

    def __str__(self):
        return (f"{self.label} ({self.alias}): {self.description} "
                f"{self.qid.url()}")
