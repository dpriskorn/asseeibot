from __future__ import annotations

import logging
from os.path import exists
from typing import TYPE_CHECKING, Optional

import pandas as pd  # type: ignore
from pandas import DataFrame
from pydantic import BaseModel


if TYPE_CHECKING:
    from asseeibot.models.crossref_engine.ontology_based_ner_matcher import FuzzyMatch

logger = logging.getLogger(__name__)


class PickledDataframe(BaseModel):
    __pickle_filename__: Optional[str]
    dataframe: DataFrame = None
    match: Optional[FuzzyMatch] = None

    class Config:
        arbitrary_types_allowed = True

    def __read_dataframe_from_disk__(self):
        self.dataframe = pd.read_pickle(self.__pickle_filename__)

    def __save_dataframe_to_disk__(self):
        self.dataframe.to_pickle(self.__pickle_filename__)

    def __verify_that_the_cache_file_exists_and_read__(self):
        """This is the method we use to read the dataframe"""
        logger.debug(f"__verify_that_the_cache_file_exists_and_read__: {self.__pickle_filename__}")
        if self.__pickle_filename__ is None:
            raise ValueError("__pickle_filename was None")
        if not exists(self.__pickle_filename__):
            logger.error(f"Pickle file {self.__pickle_filename__} not found.")
        else:
            self.__read_dataframe_from_disk__()
