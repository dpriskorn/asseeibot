from typing import Optional, List, Any

from pydantic import BaseModel


class CrossrefAuthor(BaseModel):
    given: Optional[str]
    family: Optional[str]
    sequence: Optional[str]
    affiliation: Optional[List[Any]]