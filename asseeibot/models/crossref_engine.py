import logging
from typing import Optional, TYPE_CHECKING, Dict, Any

from habanero import Crossref
from pydantic import BaseModel

from asseeibot.models.crossref_enums import CrossrefEntryType
from asseeibot.models.crossref_work import CrossrefWork


class CrossrefEngine(BaseModel):
    doi: Any

    def __post_init_post_parse__(self):
        self.__lookup_work__()

    def __lookup_work__(self) -> Optional[CrossrefWork]:
        """Lookup data and populate the object"""
        logger = logging.getLogger(__name__)
        # https://www.crossref.org/education/retrieve-metadata/rest-api/
        # async client here https://github.com/izihawa/aiocrossref but only 1 contributor
        # https://github.com/sckott/habanero >6 contributors not async
        print("Looking up from Crossref")
        cr = Crossref()
        # result = cr.works(doi=doi)
        result = cr.works(ids=self.doi.value)
        # print(result.keys())
        if "message" in result:
            self.data = result["message"]
            # pprint(self.data)
        # exit(0)
        if "type" in self.data:
            self.object_type = CrossrefEntryType(self.data["type"])
            if self.object_type == "book":
                logger.info("Book detected, we exclude those for now.")
                return None
            else:
                return CrossrefWork(**self.data)
                # print(self.__dict__)
                # exit(0)
        else:
            raise ValueError("type not found")

    data: Dict[str, Any] = None
