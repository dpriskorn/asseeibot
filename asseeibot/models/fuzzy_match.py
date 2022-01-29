from typing import Optional

from pydantic import BaseModel

from asseeibot.models.wikimedia.wikidata.entity import EntityId


class FuzzyMatch(BaseModel):
    qid: EntityId
    original_subject: str
    alias: Optional[str]
    label: Optional[str]
    description: Optional[str]

    def __str__(self):
        return (f"{self.label} ({self.alias}): {self.description} "
                f"{self.qid.url()}")
