import logging
from enum import Enum
from typing import Optional

import pandas as pd
from pandas import DataFrame

import config
from asseeibot.models.cache import Cache
from asseeibot.models.fuzzy_match import FuzzyMatch, MatchBasedOn
from asseeibot.models.ontology_dataframe import OntologyDataframeColumn
from asseeibot.models.wikimedia.wikidata.entity import EntityId

logger = logging.getLogger(__name__)


# This code is adapted from https://github.com/dpriskorn/WikidataMLSuggester and LexUtils

# lookups where inspired by
# https://stackoverflow.com/questions/24761133/pandas-check-if-row-exists-with-certain-values


class CacheDataframeColumn(Enum):
    QID = "qid"
    CROSSREF_SUBJECT = "crossref_subject"
    MATCH_BASED_ON = "match_based_on"
    SPLIT_SUBJECT = "split_subject"
    ORIGINAL_SUBJECT = "original_subject"


class MatchCache(Cache):
    """This models our cache of matches"""
    crossref_subject_found: bool = None
    dataframe: DataFrame = None
    qid_dropped: bool = None
    qid_found: bool = None
    pickle: str = config.cache_pickle_filename

    class Config:
        # Because of DataFrame
        arbitrary_types_allowed = True

    def __check_variables__(self):
        logger.debug("Checking variables")
        if (
                self.match.qid is None or
                self.match.edited_qid is None or
                self.match.crossref_subject is None or
                self.match.split_subject is None or
                self.match.match_based_on
        ):
            raise ValueError("we did not get all we need")

    def __append_new_match_to_the_dataframe__(self):
        self.__check_variables__()
        logger.debug("Adding to cache")
        data = {
            CacheDataframeColumn.QID.value: self.match.qid.value,
            CacheDataframeColumn.CROSSREF_SUBJECT: self.match.crossref_subject,
            CacheDataframeColumn.MATCH_BASED_ON: self.match.match_based_on.value,
            CacheDataframeColumn.ORIGINAL_SUBJECT: self.match.original_subject,
            CacheDataframeColumn.SPLIT_SUBJECT: self.match.split_subject,
        }
        # We only give save the value once for now
        self.dataframe = self.dataframe.append(pd.DataFrame(data=[data]))

    def __check_crossref_subject__(self):
        if self.match.crossref_subject is None:
            raise ValueError("crossref_subject was None")
        if self.match.crossref_subject == "":
            raise ValueError("crossref_subject was empty string")

    def __check_qid__(self):
        if self.match.qid is None:
            raise ValueError("qid was None")

    def __check_if_drop_was_successful__(self):
        if config.loglevel == logging.DEBUG:
            logging.debug("Checking if the qid is still in the cache")
            match = (self.dataframe[CacheDataframeColumn.QID.value] == self.match.qid.value).any()
            logger.debug(f"match:{match}")
            print(self.dataframe.info())
            logger.debug(f"Saving pickle without {self.match.qid.value}")

    def __drop_qid_from_dataframe__(self):
        self.__read_dataframe_from_disk__()
        # This tests whether any row matches
        match = (self.dataframe[CacheDataframeColumn.QID.value] == self.match.qid.value).any()
        logger.debug(f"match:{match}")
        if match:
            logger.debug("Deleting the item from the cache now")
            self.dataframe = self.dataframe[self.dataframe[CacheDataframeColumn.QID.value] != self.match.qid.value]
            self.qid_dropped = True
        else:
            self.qid_dropped = False

    def __extract_match__(self):
        """Here we find the row that matches and extract the
        result column and extract the value using any()
        """
        found_match = self.dataframe.loc[
            self.dataframe[CacheDataframeColumn.CROSSREF_SUBJECT.value] == self.match.crossref_subject].any()
        logger.debug(f"result:{found_match}")
        if found_match is not None:
            logger.info("Already matched QID found in the cache")
            row = self.dataframe[CacheDataframeColumn.CROSSREF_SUBJECT.value] == self.match.crossref_subject
            qid: EntityId = EntityId(row[CacheDataframeColumn.QID.value].value[0])
            original_subject: str = row[CacheDataframeColumn.ORIGINAL_SUBJECT.value].value[0]
            crossref_subject: str = row[CacheDataframeColumn.ORIGINAL_SUBJECT.value].value[0]
            match_based_on = MatchBasedOn(row[CacheDataframeColumn.MATCH_BASED_ON.value].value[0])
            split_subject: bool = bool(row[CacheDataframeColumn.SPLIT_SUBJECT.value].value[0])
            label = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == qid.url(),
                OntologyDataframeColumn.LABEL.value].head(1).values[0]
            description = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == qid.url(),
                OntologyDataframeColumn.DESCRIPTION.value].head(1).values[0]
            alias = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == qid.url(),
                OntologyDataframeColumn.ALIAS.value].head(1).values[0]
            self.match = FuzzyMatch(
                qid=qid,
                original_subject=original_subject,
                match_based_on=match_based_on,
                split_subject=split_subject,
                crossref_subject=crossref_subject,
                alias=alias,
                label=label,
                description=description,
            )

    def __lookup_crossref_subject__(self):
        if len(self.dataframe) > 0:
            match = (self.dataframe[CacheDataframeColumn.CROSSREF_SUBJECT.value] == self.match.crossref_subject).any()
            logger.debug(f"match:{match}")
            self.crossref_subject_found = match
        else:
            self.crossref_subject_found = False

    def __lookup_qid__(self):
        match = (self.dataframe[CacheDataframeColumn.QID.value] == self.match.qid.value).any()
        logger.debug(f"match:{match}")
        self.qid_found = match

    def read(self) -> Optional[FuzzyMatch]:
        """Returns None or result from the cache"""
        self.__check_crossref_subject__()
        self.__read_dataframe_from_disk__()
        self.__lookup_crossref_subject__()
        if self.crossref_subject_found:
            self.__extract_match__()
            return self.match

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
