from enum import Enum

import pandas as pd

import asseeibot.runtime_variables


class OntologyDataframeColumn(Enum):
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
        if asseeibot.runtime_variables.ontology_dataframe is None:
            # This pickle is ~4MB in size and takes less than a second to load.
            # noinspection PyUnresolvedReferences
            try:
                dataframe: Dataset["item", "itemLabel", "alias"] = pd.read_pickle("ontology.pkl")
            except:
                raise
            # This is needed for the fuzzymatching to work properly
            asseeibot.runtime_variables.ontology_dataframe = dataframe.fillna('')

    def __download_the_ontology_pickle__(self):
        raise NotImplementedError
