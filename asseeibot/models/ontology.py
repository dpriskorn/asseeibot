import logging
from typing import Optional

from fuzzywuzzy import fuzz
from pandas import DataFrame
from pydantic import BaseModel, PositiveInt

import config
from asseeibot.helpers.console import console
from asseeibot.helpers.util import yes_no_question
from asseeibot.models.cache import Cache
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.wikimedia.enums import DataFrameColumns
from asseeibot.models.wikimedia.wikidata.entity import EntityId
from asseeibot.models.wikimedia.wikidata.search import string_search_url


class Ontology(BaseModel):
    subject: str
    original_subject: str
    dataframe: DataFrame = None

    class Config:
        arbitrary_types_allowed = True

    def get_the_dataframe_from_config(self):
        # This has been populated by __prepare_the_dataframe__()
        self.dataframe = config.ontology_dataframe

    def lookup_subject(self) -> Optional[FuzzyMatch]:
        """Looks up the subject in the ontology and triy to fuzzymatch it to a QID"""
        if not isinstance(self.subject, str):
            raise TypeError(f"subject was '{self.subject}' which is not a string")
        if not isinstance(self.original_subject, str):
            raise TypeError(f"subject was '{self.original_subject}' which is not a string")
        logger = logging.getLogger(__name__)
        self.get_the_dataframe_from_config()
        if self.subject != self.original_subject:
            console.print(f"Trying now to match [bold green]'{self.subject}'[/bold green] which comes "
                          f"from the string '{self.original_subject}' found in Crossref")
        else:
            console.print(f"Trying now to match [bold green]'{self.subject}'[/bold green] which was found in Crossref")
        if self.subject is None or self.subject == "":
            return
        cache_match = self.lookup_in_cache()
        if cache_match is not None:
            return cache_match
        self.calculate_scores()
        label_score, alias_score, top_label_match, top_alias_match = self.extract_top_matches()
        if label_score >= alias_score:
            if label_score >= config.label_threshold_ratio:
                answer = yes_no_question("Does this match?\n"
                                         f"{str(top_label_match)}")
                if answer:
                    cache_instance = Cache()
                    cache_instance.add(label=self.subject, qid=top_label_match.qid.value)
                    return top_label_match
        if alias_score >= config.alias_threshold_ratio:
            answer = yes_no_question("Does this match?\n"
                                     f"{str(top_alias_match)}")
            if answer:
                cache_instance = Cache()
                cache_instance.add(label=self.subject, qid=top_alias_match.qid.value)
                return top_alias_match
        # None of the ratios reached the threshold
        # We probably have either a gap in our ontology or in Wikidata
        logger.warning(f"No match with a sufficient rating found. "
                       f"Search for the subject on Wikidata: "
                       f"{string_search_url(string=self.subject)}")
        # exit()

    def extract_top_match_row(self):
        """Get the first row"""
        for row in self.dataframe.itertuples(index=False):
            # This is a NamedTuple
            return row

    def extract_top_match_score(self, column: DataFrameColumns) -> PositiveInt:
        if not (column == DataFrameColumns.ALIAS or column == DataFrameColumns.LABEL):
            raise ValueError("did not get a column we support")
        row = self.extract_top_match_row()
        if column == DataFrameColumns.LABEL:
            return row.label_score
        else:
            return row.alias_score

    def extract_top_matches(self):
        if self.original_subject is None:
            raise ValueError("self.original_subject was None")
        self.dataframe = self.dataframe.sort_values("label_score", ascending=False)
        label_score = self.extract_top_match_score(column=DataFrameColumns.LABEL)
        if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
            self.print_dataframe_head()
        top_label_match = self.get_top_match()
        self.dataframe = self.dataframe.sort_values("alias_score", ascending=False)
        alias_score = self.extract_top_match_score(column=DataFrameColumns.ALIAS)
        if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
            self.print_dataframe_head()
        top_alias_match = self.get_top_match()
        return label_score, alias_score, top_label_match, top_alias_match

    def get_top_match(self):
        if self.original_subject is None:
            raise ValueError("self.original_subject was None")
        row = self.extract_top_match_row()
        # logger.debug(f"row:{row}")

        # present the match
        return FuzzyMatch(**dict(
            qid=EntityId(row.item),
            alias=row.alias,
            label=row.label,
            description=row.description,
            original_subject=self.original_subject
        ))

    def lookup_in_cache(self):
        logger = logging.getLogger(__name__)
        cache = Cache()
        qid = cache.read(label=self.subject)
        if qid is not None:
            logger.info("Already matched QID found in the cache")
            # result = df.loc[df["label"] == label, "qid"][0]
            label = self.dataframe.loc[
                self.dataframe[DataFrameColumns.ITEM.value] == f"{config.wd_prefix}{qid}",
                DataFrameColumns.LABEL.value].head(1).values[0]
            description = self.dataframe.loc[
                self.dataframe[DataFrameColumns.ITEM.value] == f"{config.wd_prefix}{qid}",
                DataFrameColumns.DESCRIPTION.value].head(1).values[0]
            alias = self.dataframe.loc[
                self.dataframe[DataFrameColumns.ITEM.value] == f"{config.wd_prefix}{qid}",
                DataFrameColumns.ALIAS.value].head(1).values[0]
            return FuzzyMatch(
                qid=EntityId(raw_entity_id=qid),
                label=label,
                alias=alias,
                description=description,
                original_subject=self.original_subject
            )

    def calculate_scores(self):
        logger = logging.getLogger(__name__)
        logger.debug(f"Calculating scores")
        # This code is inspired by Nikhil VJ
        # https://stackoverflow.com/questions/38577332/apply-fuzzy-matching-across-a-dataframe-column-and-save-results-in-a-new-column
        self.dataframe["label_score"] = self.dataframe.label.apply(lambda x: fuzz.ratio(x, self.subject))
        self.dataframe["alias_score"] = self.dataframe.alias.apply(lambda x: fuzz.ratio(x, self.subject))
        # print(self.dataframe.head())

    def print_dataframe_head(self):
        print(self.dataframe.head(2))
