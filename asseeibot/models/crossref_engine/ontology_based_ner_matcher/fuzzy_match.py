from typing import Optional

from pydantic import BaseModel

from asseeibot.models.enums import MatchBasedOn
from asseeibot.models.wikimedia.wikidata.entity_id import EntityId


class FuzzyMatch(BaseModel):
    crossref_subject: Optional[str]
    qid: Optional[EntityId]
    edited_qid: Optional[EntityId]
    match_based_on: Optional[MatchBasedOn]
    original_subject: Optional[str]
    split_subject: Optional[bool]
    approved: Optional[bool]
    alias: Optional[str]
    label: Optional[str]
    description: Optional[str]

    def __str__(self):
        return (f"[bold green]{self.label}[/bold green] ({self.alias}): {self.description} "
                f"{self.qid.url()}")
