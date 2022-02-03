from pydantic import BaseModel


# @dataclass
class Identifier(BaseModel):
    """Base model for an identifier"""
    value: str

    def __str__(self):
        return self.value
