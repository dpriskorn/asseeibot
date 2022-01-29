from enum import Enum

import pandas as pd

import config


class DataframeColumn(Enum):
    """These are special to our ontology, but they are standard names in WDQS"""
    ALIAS = "alias"
    DESCRIPTION = "description"
    ITEM = "item"
    LABEL = "label"
    LABEL_SCORE = "label_score"
    ALIAS_SCORE = "alias_score"


class Dataframe:
    @staticmethod
    def prepare_the_dataframe():
        # self.__download_the_ontology_pickle__()
        if config.ontology_dataframe is None:
            # This pickle is ~4MB in size and takes less than a second to load.
            # noinspection PyUnresolvedReferences
            dataframe: Dataset["item", "itemLabel", "alias"] = pd.read_pickle("ontology.pkl")
            # This is needed for the fuzzymatching to work properly
            config.ontology_dataframe = dataframe.fillna('')

    def __download_the_ontology_pickle__(self):
        raise NotImplementedError
