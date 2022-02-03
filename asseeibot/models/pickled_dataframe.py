from __future__ import annotations

import logging
from os.path import exists
from typing import TYPE_CHECKING

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

if TYPE_CHECKING:
    from asseeibot import FuzzyMatch

logger = logging.getLogger(__name__)


class PickledDataframe(BaseModel):
    __pickle_filename: str = None
    dataframe: DataFrame = None
    match: FuzzyMatch = None

    class Config:
        arbitrary_types_allowed = True

    def __read_dataframe_from_disk__(self):
        self.dataframe = pd.read_pickle(self.__pickle_filename)

    def __save_dataframe_to_disk__(self):
        self.dataframe.to_pickle(self.__pickle_filename)

    def __verify_that_the_cache_file_exists_and_read__(self):
        if self.__pickle_filename is None:
            raise ValueError("pickle was None")
        if not exists(self.__pickle_filename):
            logger.error(f"Pickle file {self.__pickle_filename} not found.")
        else:
            self.__read_dataframe_from_disk__()

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
