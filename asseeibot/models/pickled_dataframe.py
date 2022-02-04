from __future__ import annotations

import logging
from os.path import exists
from typing import TYPE_CHECKING, Optional

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

if TYPE_CHECKING:
    from asseeibot import FuzzyMatch

logger = logging.getLogger(__name__)


class PickledDataframe(BaseModel):
    _pickle_filename: Optional[str]
    dataframe: DataFrame = None
    match: FuzzyMatch = None

    class Config:
        arbitrary_types_allowed = True

    def __read_dataframe_from_disk__(self):
        self.dataframe = pd.read_pickle(self._pickle_filename)

    def __save_dataframe_to_disk__(self):
        self.dataframe.to_pickle(self._pickle_filename)

    def __verify_that_the_cache_file_exists_and_read__(self):
        """This is the method we use to read the dataframe"""
        logger.debug(f"__verify_that_the_cache_file_exists_and_read__: {self._pickle_filename}")
        if self._pickle_filename is None:
            raise ValueError("__pickle_filename was None")
        if not exists(self._pickle_filename):
            logger.error(f"Pickle file {self._pickle_filename} not found.")
        else:
            self.__read_dataframe_from_disk__()
