import logging
from datetime import datetime

import pandas as pd

import config
from asseeibot.models.enums import StatisticDataframeColumn
from asseeibot.models.pickled_dataframe import PickledDataframe

logger = logging.getLogger(__name__)


class StatisticPickledDataframe(PickledDataframe):
    """This class stores all uploaded data to a dataframe
    It makes it easy to follow edits over time"""
    __pickle: str = config.statistic_pickle_filename

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

    class Config:
        arbitrary_types_allowed = True

    def __append_to_the_dataframe__(self):
        logger.debug("Adding to cache")
        if self.match is None:
            raise ValueError("match was None")
        if self.match.crossref_subject is None:
            raise ValueError("match.crossref_subject was None")
        data = {
            StatisticDataframeColumn.EDITED_QID.value: self.match.edited_qid.value,
            StatisticDataframeColumn.SUBJECT_QID.value: self.match.qid.value,
            StatisticDataframeColumn.CROSSREF_SUBJECT.value: self.match.crossref_subject,
            StatisticDataframeColumn.MATCH_BASED_ON.value: self.match.match_based_on.value,
            StatisticDataframeColumn.ORIGINAL_SUBJECT.value: self.match.original_subject,
            StatisticDataframeColumn.SPLIT_SUBJECT.value: self.match.split_subject,
            StatisticDataframeColumn.DATETIME.value: datetime.now(),
            StatisticDataframeColumn.ROLLED_BACK.value: False,
        }
        # We only give save the value once for now
        if self.dataframe is None or len(self.dataframe) == 0:
            self.dataframe = pd.DataFrame(data=[data])
        else:
            self.dataframe = self.dataframe.append(pd.DataFrame(data=[data]))

    def add(self):
        """Add an uploaded match to the dataframe"""
        self.__verify_that_the_cache_file_exists_and_read__()
        self.__append_to_the_dataframe__()
        self.__save_dataframe_to_disk__()
