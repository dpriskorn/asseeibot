import logging
from enum import Enum
from os.path import exists
from typing import Optional

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel

import config
from asseeibot.models.wikimedia.wikidata.entity import EntityId

logger = logging.getLogger(__name__)

# This code is adapted from https://github.com/dpriskorn/WikidataMLSuggester and LexUtils

# lookups where inspired by
# https://stackoverflow.com/questions/24761133/pandas-check-if-row-exists-with-certain-values


class CacheDataframeColumn(Enum):
    QID = "qid"
    CROSSREF_SUBJECT = "crossref_subject"


class Cache(BaseModel):
    """This models our cache of matches"""
    qid: Optional[EntityId]
    crossref_subject: Optional[str]
    crossref_subject_found: bool = None
    matched_qid: EntityId = None
    dataframe: DataFrame = None
    qid_dropped: bool = None
    qid_found: bool = None
    pickle: str = config.cache_pickle_filename

    class Config:
        # Because of DataFrame
        arbitrary_types_allowed = True

    def __append_new_match_to_the_dataframe__(self):
        logger.debug("Adding to cache")
        data = dict(qid=self.qid, label=self.crossref_subject)
        # We only give save the value once for now
        self.dataframe = self.dataframe.append(pd.DataFrame(data=[data]))

    def __check_crossref_subject__(self):
        if self.crossref_subject is None:
            raise ValueError("crossref_subject was None")
        if self.crossref_subject == "":
            raise ValueError("crossref_subject was empty string")

    def __check_qid__(self):
        if self.qid is None:
            raise ValueError("qid was None")

    def __check_if_drop_was_successful__(self):
        if config.loglevel == logging.DEBUG:
            logging.debug("Checking if the qid is still in the cache")
            match = (self.dataframe[CacheDataframeColumn.QID.value] == self.qid.value).any()
            logger.debug(f"match:{match}")
            print(self.dataframe.info())
            logger.debug(f"Saving pickle without {self.qid.value}")

    def __drop_qid_from_dataframe__(self):
        self.__read_dataframe_from_disk__()
        # This tests whether any row matches
        match = (self.dataframe[CacheDataframeColumn.QID.value] == self.qid.value).any()
        logger.debug(f"match:{match}")
        if match:
            logger.debug("Deleting the item from the cache now")
            self.dataframe = self.dataframe[self.dataframe[CacheDataframeColumn.QID.value] != self.qid.value]
            self.qid_dropped = True
        else:
            self.qid_dropped = False

    def __extract_match__(self):
        """Here we find the row that matches and extract the
        result column and extract the value using any()
        """
        result = self.dataframe.loc[
            self.dataframe[CacheDataframeColumn.CROSSREF_SUBJECT.value] == self.crossref_subject,
            CacheDataframeColumn.QID.value][0]
        logger.debug(f"result:{result}")
        if result is not None:
            self.matched_qid = EntityId(result)

    def __lookup_crossref_subject__(self):
        match = (self.dataframe[CacheDataframeColumn.CROSSREF_SUBJECT.value] == self.crossref_subject).any()
        logger.debug(f"match:{match}")
        self.crossref_subject_found = match

    def __lookup_qid__(self):
        match = (self.dataframe[CacheDataframeColumn.QID.value] == self.qid.value).any()
        logger.debug(f"match:{match}")
        self.qid_found = match

    def __read_dataframe_from_disk__(self):
        self.__verify_that_the_cache_file_exists__()
        self.dataframe = pd.read_pickle(self.pickle)

    def __save_dataframe_to_disk__(self):
        self.dataframe.to_pickle(self.pickle)

    def __verify_that_the_cache_file_exists__(self):
        if not exists(self.pickle):
            logger.error(f"Cachefile {self.pickle} not found.")
            exit(0)

    def read(self) -> Optional[EntityId]:
        """Returns None or result from the cache"""
        self.__check_crossref_subject__()
        self.__read_dataframe_from_disk__()
        self.__lookup_crossref_subject__()
        if self.crossref_subject_found:
            return self.__extract_match__()

    def add(self) -> bool:
        """Add a match to the cache
        It returns True if it was added and False if either QID
        or the crossref subject was found in the cache.
        :return: bool"""
        self.__check_crossref_subject__()
        self.__check_qid__()
        self.__read_dataframe_from_disk__()
        self.__lookup_crossref_subject__()
        if not self.crossref_subject_found and not self.qid_found:
            self.__append_new_match_to_the_dataframe__()
            self.__save_dataframe_to_disk__()
            return True
        else:
            return False

    def delete(self) -> bool:
        """Delete from the cache.
        Returns True if success and False if not found"""
        self.__check_qid__()
        logger.debug("Deleting from the cache")
        self.__drop_qid_from_dataframe__()
        if self.qid_dropped:
            self.__save_dataframe_to_disk__()
            return True
        else:
            return False
