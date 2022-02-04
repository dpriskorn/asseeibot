from datetime import datetime
from typing import Optional, List, Union

from pydantic import BaseModel, conint


class CrossrefDateParts(BaseModel):
    """This model date-parts in the crossref_engine API.
    They contain None sometimes."""
    date_parts: Optional[List[List[Union[conint(ge=0, lt=2023), None]]]]
    date_time: Optional[datetime]
