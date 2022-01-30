import logging
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd

import config
from asseeibot import FuzzyMatch
from asseeibot.models.cache import Cache

logger = logging.getLogger(__name__)


class StatisticDataframeColumn(Enum):
    EDITED_QID = "edited_qid"
    SUBJECT_QID = "subject_qid"
    CROSSREF_SUBJECT = "crossref_subject"
    MATCH_BASED_ON = "match_based_on"
    SPLIT_SUBJECT = "split_subject"
    ORIGINAL_SUBJECT = "original_subject"
    DATETIME = "datetime"
    ROLLED_BACK = "rolled_back"


class StatisticDataframe(Cache):
    """This class stores all uploaded data to a dataframe
    It makes it easy to follow edits over time"""
    match: Optional[FuzzyMatch]
    pickle: str = config.statistic_pickle_filename

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

    def __append_to_the_dataframe__(self):
        logger.debug("Adding to cache")
        if self.match is None:
            raise ValueError("match was None")
        data = {
            StatisticDataframeColumn.EDITED_QID.value: self.match.edited_qid.value,
            StatisticDataframeColumn.SUBJECT_QID.value: self.match.qid.value,
            StatisticDataframeColumn.CROSSREF_SUBJECT: self.match.crossref_subject,
            StatisticDataframeColumn.MATCH_BASED_ON: self.match.match_based_on.value,
            StatisticDataframeColumn.ORIGINAL_SUBJECT: self.match.original_subject,
            StatisticDataframeColumn.SPLIT_SUBJECT: self.match.split_subject,
            StatisticDataframeColumn.DATETIME: datetime.now(),
            StatisticDataframeColumn.ROLLED_BACK: False,
        }
        # We only give save the value once for now
        self.dataframe = self.dataframe.append(pd.DataFrame(data=[data]))

    def add(self):
        """Add an uploaded match to the dataframe"""
        self.__read_dataframe_from_disk__()
        self.__append_to_the_dataframe__()
        self.__save_dataframe_to_disk__()
