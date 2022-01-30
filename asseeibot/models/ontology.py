import logging
from typing import Optional

from fuzzywuzzy import fuzz
from pandas import DataFrame
from pydantic import BaseModel, PositiveInt

import asseeibot.runtime_variables
import config
from asseeibot.helpers.util import yes_no_question
from asseeibot.models.fuzzy_match import FuzzyMatch, MatchBasedOn
from asseeibot.models.match_cache import MatchCache
from asseeibot.models.ontology_dataframe import OntologyDataframeColumn
from asseeibot.models.wikimedia.wikidata.entity import EntityId
from asseeibot.models.wikimedia.wikidata.search import string_search_url

logger = logging.getLogger(__name__)


class Ontology(BaseModel):
    """This models the domain ontology and performs lookups

    :param subject: str
    :param original_subject: str
    """
    subject: str
    original_subject: str
    split_subject: bool
    dataframe: DataFrame = None
    match: Optional[FuzzyMatch] = None

    class Config:
        arbitrary_types_allowed = True

    def __check_subject_and_original_subject__(self):
        if not isinstance(self.subject, str):
            raise TypeError(f"subject was '{self.subject}' which is not a string")
        if not isinstance(self.original_subject, str):
            raise TypeError(f"subject was '{self.original_subject}' which is not a string")

    def __print_subject_information__(self):
        from asseeibot.helpers.console import console
        if self.subject != self.original_subject:
            console.print(f"Trying now to match [bold green]'{self.subject}'[/bold green] which comes "
                          f"from the string '{self.original_subject}' found in Crossref")
        else:
            console.print(f"Trying now to match [bold green]'{self.subject}'[/bold green] which was found in Crossref")

    def __check_subject__(self):
        if self.subject is None or self.subject == "":
            return

    def __validate_the_match__(self):
        if self.match is not None:
            # todo more checks
            if self.match.match_based_on is None:
                raise ValueError("self.match.match_based_on was None")

    def lookup_subject(self) -> None:
        """Looks up the subject in the ontology and try to fuzzymatch it to a QID"""
        # TODO split this up
        self.match = None
        self.__check_subject_and_original_subject__()
        self.__get_the_dataframe_from_config__()
        self.__check_subject__()
        self.__print_subject_information__()
        self.__lookup_in_cache__()
        if self.match is None:
            # We proceed if not found in the cache
            self.__calculate_scores__()
            self.__lookup_scores_and_matches_in_the_ontology__()
        self.__validate_the_match__()

    def __lookup_scores_and_matches_in_the_ontology__(self):
        label_score, alias_score, top_label_match, top_alias_match = self.__extract_top_matches__()
        if self.match is None and label_score >= alias_score:
            if label_score >= config.label_threshold_ratio:
                answer = yes_no_question("Does this match?\n"
                                         f"{str(top_label_match)}")
                if answer:
                    self.match = FuzzyMatch(
                        crossref_subject=self.subject,
                        match_based_on=MatchBasedOn.LABEL,
                        original_subject=self.original_subject,
                        qid=top_label_match.qid,
                        split_subject=self.split_subject,
                    )
                    cache_instance = MatchCache(match=self.match)
                    cache_instance.add()
        if self.match is None and alias_score >= config.alias_threshold_ratio:
            answer = yes_no_question("Does this match?\n"
                                     f"{str(top_alias_match)}")
            if answer:
                self.match = FuzzyMatch(
                    crossref_subject=self.subject,
                    match_based_on=MatchBasedOn.ALIAS,
                    original_subject=self.original_subject,
                    qid=top_alias_match.qid,
                    split_subject=self.split_subject,
                )
                cache_instance = MatchCache(match=self.match)
                cache_instance.add()
        # None of the ratios reached the threshold
        # We probably have either a gap in our ontology or in Wikidata
        logger.warning(f"No match with a sufficient rating found. ")
        logger.info(
            f"Search for the subject on Wikidata: "
            f"{string_search_url(string=self.subject)}"
        )
        # exit()

    def __calculate_scores__(self):
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

    def __extract_top_match_score__(self, column: OntologyDataframeColumn) -> PositiveInt:
        if not (column == OntologyDataframeColumn.ALIAS or column == OntologyDataframeColumn.LABEL):
            raise ValueError("did not get a column we support")
        row = self.__get_first_row__()
        if column == OntologyDataframeColumn.LABEL:
            return row.label_score
        else:
            return row.alias_score

    def __extract_top_label_match_and_score__(self):
        self.__sort_dataframe__(OntologyDataframeColumn.LABEL_SCORE)
        label_score = self.__extract_top_match_score__(column=OntologyDataframeColumn.LABEL)
        if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
            self.__print_dataframe_head__()
        return self.__get_top_match__(), label_score

    def __extract_top_alias_match_and_score__(self):
        self.__sort_dataframe__(OntologyDataframeColumn.ALIAS_SCORE)
        alias_score = self.__extract_top_match_score__(column=OntologyDataframeColumn.ALIAS)
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
            original_subject=self.original_subject,
            split_subject=self.split_subject
        ))

    def __lookup_in_cache__(self):
        cache = MatchCache(match=FuzzyMatch(
            crossref_subject=self.subject
        ))
        match = cache.read()
        if match is not None:
            logger.info("Already matched QID found in the cache")
            label = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == match.qid.url(),
                OntologyDataframeColumn.LABEL.value].head(1).values[0]
            description = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == match.qid.url(),
                OntologyDataframeColumn.DESCRIPTION.value].head(1).values[0]
            alias = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == match.qid.url(),
                OntologyDataframeColumn.ALIAS.value].head(1).values[0]
            self.match = FuzzyMatch(
                qid=match.qid,
                label=label,
                alias=alias,
                description=description,
                original_subject=match.original_subject,
                split_subject=match.split_subject,
                match_based_on=match.match_based_on
            )

    def __print_dataframe_head__(self):
        print(self.dataframe.head(2))

    def __sort_dataframe__(self, column: OntologyDataframeColumn):
        if isinstance(column, OntologyDataframeColumn):
            self.dataframe = self.dataframe.sort_values(column.value, ascending=False)
        else:
            raise ValueError(f"{column} is not a DataframeColumns")
