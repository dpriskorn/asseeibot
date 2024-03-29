from pydantic import BaseModel


# @dataclass
class Identifier(BaseModel):
    """Base model for an identifier"""
    value: str
    found_in_wikidata: bool = False

    def __str__(self):
        return self.value
