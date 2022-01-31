from __future__ import annotations

import logging
from os.path import exists
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import BaseModel

if TYPE_CHECKING:
    from asseeibot import FuzzyMatch

logger = logging.getLogger(__name__)


class Cache(BaseModel):
    match: FuzzyMatch
    pickle: str

    # def __init__(self):
    #     self.match = FuzzyMatch(
    #         qid=qid,
    #         original_subject=original_subject,
    #         match_based_on=match_based_on,
    #         split_subject=split_subject,
    #         crossref_subject=crossref_subject,
    #         alias=alias,
    #         label=label,
    #         description=description,
    #     )

    # def __create_dataframe__(self):
    #     self.dataframe = pd.DataFrame()
    #     self.__save_dataframe_to_disk__()

    def __read_dataframe_from_disk__(self):
        self.dataframe = pd.read_pickle(self.pickle)

    def __save_dataframe_to_disk__(self):
        self.dataframe.to_pickle(self.pickle)

    def __verify_that_the_cache_file_exists_and_read__(self):
        if not exists(self.pickle):
            logger.error(f"Pickle file {self.pickle} not found.")
        else:
            self.__read_dataframe_from_disk__()
