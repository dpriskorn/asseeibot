import logging
from typing import Optional

from fuzzywuzzy import fuzz
from pandas import DataFrame
from pydantic import BaseModel, PositiveInt

import asseeibot.runtime_variables
import config
from asseeibot import Matches
from asseeibot.helpers.runtime_variable_setup import prepare_the_ontology_pickled_dataframe
from asseeibot.helpers.util import yes_no_question
from asseeibot.helpers.wikidata import string_search_url
from asseeibot.models.crossref_engine.ontology_based_ner_matcher.fuzzy_match import FuzzyMatch
from asseeibot.models.enums import OntologyDataframeColumn, MatchBasedOn
from asseeibot.models.wikimedia.wikidata.entity_id import EntityId

logger = logging.getLogger(__name__)


class OntologyBasedNerMatcher(BaseModel):
    """This models the domain ontology and performs lookups

    :param subject: str
    :param original_subject: str
    """
    # TODO consider splitting this it up so it does not both handle cache and ontology lookups
    crossref_subject: str
    original_subject: str
    split_subject: bool
    dataframe: DataFrame = None
    match: Optional[FuzzyMatch] = None

    class Config:
        arbitrary_types_allowed = True

    def __check_subject_and_original_subject__(self):
        if not isinstance(self.crossref_subject, str):
            raise TypeError(f"subject was '{self.crossref_subject}' which is not a string")
        if not isinstance(self.original_subject, str):
            raise TypeError(f"subject was '{self.original_subject}' which is not a string")

    def __calculate_scores__(self):
        logger.debug(f"Calculating scores")
        if self.dataframe is None:
            raise ValueError("self.dataframe was None")
        # This code is inspired by Nikhil VJ
        # https://stackoverflow.com/questions/38577332/apply-fuzzy-matching-across-a-dataframe-column-and-save-results-in-a-new-column
        # We lowercase the string to avoid having the same ratio
        # on petrology->Petrology as petrology->metrology
        self.dataframe["label_score"] = self.dataframe.label.apply(
            lambda x: fuzz.ratio(x.lower(), self.crossref_subject.lower())
        )
        self.dataframe["alias_score"] = self.dataframe.alias.apply(
            lambda x: fuzz.ratio(x.lower(), self.crossref_subject.lower())
        )

    def __enrich_cache_match__(self):
        if self.match is not None:
            logger.info("Already matched QID found in the cache")
            # We enrich the match from the cache before returning it
            self.match.label = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == self.match.qid.url(),
                OntologyDataframeColumn.LABEL.value].head(1).values[0]
            self.match.description = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == self.match.qid.url(),
                OntologyDataframeColumn.DESCRIPTION.value].head(1).values[0]
            self.match.alias = self.dataframe.loc[
                self.dataframe[OntologyDataframeColumn.ITEM.value] == self.match.qid.url(),
                OntologyDataframeColumn.ALIAS.value].head(1).values[0]

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
        if asseeibot.runtime_variables.ontology_dataframe is None:
            prepare_the_ontology_pickled_dataframe()
        self.dataframe = asseeibot.runtime_variables.ontology_dataframe
        # raise RuntimeError("config.ontology_dataframe was None")

    def __get_top_match__(self):
        if self.original_subject is None:
            raise ValueError("self.original_subject was None")
        row = self.__get_first_row__()
        # logger.debug(f"row:{row}")
        # present the match
        if row.label is None:
            raise ValueError("row.label was None")
        return FuzzyMatch(**dict(
            qid=EntityId(row.item),
            alias=row.alias,
            label=row.label,
            description=row.description,
            original_subject=self.original_subject,
            split_subject=self.split_subject,
            match_based_on=None
        ))

    def __lookup_in_cache__(self):
        cache = Matches(crossref_subject=self.crossref_subject)
        cache.read()
        if cache.crossref_subject_found:
            if config.loglevel == logging.DEBUG:
                from asseeibot.helpers.console import console
                console.print(cache.dict())
            self.match = cache.match
            if self.match.approved:
                self.__enrich_cache_match__()
        else:
            logger.info(f"No match in cache for {self.crossref_subject}")

    def __lookup_scores_and_matches_in_the_ontology__(self):
        label_score, alias_score, top_label_match, top_alias_match = self.__extract_top_matches__()
        if self.match is None and label_score >= alias_score:
            logger.debug("Matching on original subject and label")
            if label_score >= config.label_threshold_ratio:
                if config.loglevel == logging.DEBUG:
                    from asseeibot.helpers.console import console
                    console.print(top_label_match.dict())
                answer = yes_no_question("Does this match?\n"
                                         f"{str(top_label_match)}")
                if answer:
                    approved = True
                else:
                    approved = False
                self.match = FuzzyMatch(
                    label=top_label_match.label,
                    alias=top_label_match.alias,
                    description=top_label_match.description,
                    crossref_subject=self.crossref_subject,
                    match_based_on=MatchBasedOn.LABEL,
                    original_subject=self.original_subject,
                    qid=top_label_match.qid,
                    split_subject=self.split_subject,
                    approved=approved,
                )
                cache_instance = Matches(match=self.match,
                                         crossref_subject=self.crossref_subject)
                cache_instance.add()
        elif self.match is None and alias_score >= config.alias_threshold_ratio:
            logger.debug("Matching on original subject and alias")
            if config.loglevel == logging.DEBUG:
                from asseeibot.helpers.console import console
                console.print(top_alias_match.dict())
            answer = yes_no_question("Does this match?\n"
                                     f"{str(top_alias_match)}")
            if answer:
                approved = True
            else:
                approved = False
            self.match = FuzzyMatch(
                label=top_alias_match.label,
                alias=top_alias_match.alias,
                description=top_alias_match.description,
                crossref_subject=self.crossref_subject,
                match_based_on=MatchBasedOn.ALIAS,
                original_subject=self.original_subject,
                qid=top_alias_match.qid,
                split_subject=self.split_subject,
                approved=approved,
            )
            cache_instance = Matches(match=self.match,
                                     crossref_subject=self.crossref_subject)
            cache_instance.add()
        else:
            # None of the ratios reached the threshold
            # We probably have either a gap in our ontology or in Wikidata
            logger.warning(f"No match with a sufficient rating found.")
            logger.info(
                f"Search for the subject on Wikidata: "
                f"{string_search_url(string=self.crossref_subject)}"
            )
            # exit()

    def __print_dataframe_head__(self):
        print(self.dataframe.head(2))

    def __print_subject_information__(self):
        from asseeibot.helpers.console import console
        if self.crossref_subject != self.original_subject:
            console.print(f"Trying now to match [bold green]'{self.crossref_subject}'[/bold green] which comes "
                          f"from the string '{self.original_subject}' found in Crossref")
        else:
            console.print(
                f"Trying now to match [bold green]'{self.crossref_subject}'[/bold green] which was found in Crossref")

    def __sort_dataframe__(self, column: OntologyDataframeColumn):
        if isinstance(column, OntologyDataframeColumn):
            self.dataframe = self.dataframe.sort_values(column.value, ascending=False)
        else:
            raise ValueError(f"{column} is not a DataframeColumns")

    def __validate_the_match__(self):
        if self.match.match_based_on is None:
            raise ValueError("match.match_based_on was None")
        if self.match.crossref_subject is None:
            raise ValueError("match.crossref_subject was None ")
        if self.match.qid is None:
            raise ValueError("match.qid was None ")
        if self.match.split_subject is None:
            raise ValueError("match.split_subject was None ")
        if self.match.original_subject is None:
            raise ValueError("match.original_subject was None ")
        if self.match.label is None:
            raise ValueError("match.label was None ")

    def lookup_subject(self) -> None:
        """Looks up the subject in the ontology and try to fuzzymatch it to a QID"""
        self.match = None
        self.__check_subject_and_original_subject__()
        self.__get_the_dataframe_from_config__()
        self.__print_subject_information__()
        self.__lookup_in_cache__()
        if self.match is not None:
            self.__validate_the_match__()
        if self.match is None:
            logger.info(f"We proceed to look up in the ontology "
                        f"because we could not a match for {self.crossref_subject} in the cache")
            self.__calculate_scores__()
            self.__lookup_scores_and_matches_in_the_ontology__()
            if self.match is not None:
                self.__validate_the_match__()
