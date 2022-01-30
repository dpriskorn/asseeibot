import logging
from typing import Optional

from fuzzywuzzy import fuzz
from pandas import DataFrame
from pydantic import BaseModel, PositiveInt

import asseeibot.runtime_variables
import config
from asseeibot.helpers.util import yes_no_question
from asseeibot.models.cache import Cache
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.dataframe import DataframeColumn
from asseeibot.models.wikimedia.wikidata.entity import EntityId
from asseeibot.models.wikimedia.wikidata.search import string_search_url


class Ontology(BaseModel):
    """This models the domain ontology and performs lookups

    :param subject: str
    :param original_subject: str
    """
    subject: str
    original_subject: str
    dataframe: DataFrame = None

    class Config:
        arbitrary_types_allowed = True

    def lookup_subject(self) -> Optional[FuzzyMatch]:
        """Looks up the subject in the ontology and triy to fuzzymatch it to a QID"""
        if not isinstance(self.subject, str):
            raise TypeError(f"subject was '{self.subject}' which is not a string")
        if not isinstance(self.original_subject, str):
            raise TypeError(f"subject was '{self.original_subject}' which is not a string")
        logger = logging.getLogger(__name__)
        self.__get_the_dataframe_from_config__()
        from asseeibot.helpers.console import console
        if self.subject != self.original_subject:
            console.print(f"Trying now to match [bold green]'{self.subject}'[/bold green] which comes "
                          f"from the string '{self.original_subject}' found in Crossref")
        else:
            console.print(f"Trying now to match [bold green]'{self.subject}'[/bold green] which was found in Crossref")
        if self.subject is None or self.subject == "":
            return
        cache_match = self.__lookup_in_cache__()
        if cache_match is not None:
            return cache_match
        self.__calculate_scores__()
        label_score, alias_score, top_label_match, top_alias_match = self.__extract_top_matches__()
        if label_score >= alias_score:
            if label_score >= config.label_threshold_ratio:
                answer = yes_no_question("Does this match?\n"
                                         f"{str(top_label_match)}")
                if answer:
                    cache_instance = Cache(crossref_subject=self.subject, qid=top_label_match.qid)
                    cache_instance.add()
                    return top_label_match
        if alias_score >= config.alias_threshold_ratio:
            answer = yes_no_question("Does this match?\n"
                                     f"{str(top_alias_match)}")
            if answer:
                cache_instance = Cache(crossref_subject=self.subject, qid=top_alias_match.qid)
                cache_instance.add()
                return top_alias_match
        # None of the ratios reached the threshold
        # We probably have either a gap in our ontology or in Wikidata
        logger.warning(f"No match with a sufficient rating found. "
                       f"Search for the subject on Wikidata: "
                       f"{string_search_url(string=self.subject)}")
        # exit()

    def __calculate_scores__(self):
        logger = logging.getLogger(__name__)
        logger.debug(f"Calculating scores")
        # This code is inspired by Nikhil VJ
        # https://stackoverflow.com/questions/38577332/apply-fuzzy-matching-across-a-dataframe-column-and-save-results-in-a-new-column
        # We lowercase the string to avoid having the same ratio
        # on petrology->Petrology as petrology->metrology
        self.dataframe["label_score"] = self.dataframe.label.apply(
            lambda x: fuzz.ratio(x.lower(), self.subject.lower())
        )
        self.dataframe["alias_score"] = self.dataframe.alias.apply(
            lambda x: fuzz.ratio(x.lower(), self.subject.lower())
        )

    def __extract_top_match_score__(self, column: DataframeColumn) -> PositiveInt:
        if not (column == DataframeColumn.ALIAS or column == DataframeColumn.LABEL):
            raise ValueError("did not get a column we support")
        row = self.__get_first_row__()
        if column == DataframeColumn.LABEL:
            return row.label_score
        else:
            return row.alias_score

    def __extract_top_label_match_and_score__(self):
        self.__sort_dataframe__(DataframeColumn.LABEL_SCORE)
        label_score = self.__extract_top_match_score__(column=DataframeColumn.LABEL)
        if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
            self.__print_dataframe_head__()
        return self.__get_top_match__(), label_score

    def __extract_top_alias_match_and_score__(self):
        self.__sort_dataframe__(DataframeColumn.ALIAS_SCORE)
        alias_score = self.__extract_top_match_score__(column=DataframeColumn.ALIAS)
        if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
            self.__print_dataframe_head__()
        return self.__get_top_match__(), alias_score

    def __extract_top_matches__(self):
        if self.original_subject is None:
            raise ValueError("self.original_subject was None")
        top_label_match, label_score = self.__extract_top_label_match_and_score__()
        top_alias_match, alias_score = self.__extract_top_alias_match_and_score__()
        return label_score, alias_score, top_label_match, top_alias_match

    def __get_first_row__(self):
        """Get the first row"""
        for row in self.dataframe.itertuples(index=False):
            # This is a NamedTuple
            return row

    def __get_the_dataframe_from_config__(self):
        # This has been populated by __prepare_the_dataframe__()
        if asseeibot.runtime_variables.ontology_dataframe is not None:
            self.dataframe = asseeibot.runtime_variables.ontology_dataframe
        else:
            raise RuntimeError("config.ontology_dataframe was None")

    def __get_top_match__(self):
        if self.original_subject is None:
            raise ValueError("self.original_subject was None")
        row = self.__get_first_row__()
        # logger.debug(f"row:{row}")

        # present the match
        return FuzzyMatch(**dict(
            qid=EntityId(row.item),
            alias=row.alias,
            label=row.label,
            description=row.description,
            original_subject=self.original_subject
        ))

    def __lookup_in_cache__(self):
        logger = logging.getLogger(__name__)
        cache = Cache(crossref_subject=self.subject)
        qid = cache.read()
        if qid is not None:
            logger.info("Already matched QID found in the cache")
            label = self.dataframe.loc[
                self.dataframe[DataframeColumn.ITEM.value] == qid.url(),
                DataframeColumn.LABEL.value].head(1).values[0]
            description = self.dataframe.loc[
                self.dataframe[DataframeColumn.ITEM.value] == qid.url(),
                DataframeColumn.DESCRIPTION.value].head(1).values[0]
            alias = self.dataframe.loc[
                self.dataframe[DataframeColumn.ITEM.value] == qid.url(),
                DataframeColumn.ALIAS.value].head(1).values[0]
            return FuzzyMatch(
                qid=qid,
                label=label,
                alias=alias,
                description=description,
                original_subject=self.original_subject
            )

    def __print_dataframe_head__(self):
        print(self.dataframe.head(2))

    def __sort_dataframe__(self, column: DataframeColumn):
        if isinstance(column, DataframeColumn):
            self.dataframe = self.dataframe.sort_values(column.value, ascending=False)
        else:
            raise ValueError(f"{column} is not a DataframeColumns")
