from pydantic import BaseModel

from asseeibot.models.wikimedia.wikidata_entity import EntityId


class FuzzyMatch(BaseModel):
    qid: EntityId
    label: str
    description: str

    def __str__(self):
        return (f"{self.label}: {self.description} "
                f"{self.qid.url()}")
