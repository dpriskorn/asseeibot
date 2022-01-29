import logging
import re
from typing import Optional, Set, List, Any

import pandas as pd
from dataenforce import Dataset
from fuzzywuzzy import fuzz
from pydantic import PositiveInt
from pydantic.dataclasses import dataclass

import config
from asseeibot.helpers.util import yes_no_question
from asseeibot.models.cache import Cache
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.wikimedia.enums import DataFrameColumns
from asseeibot.models.wikimedia.wikidata.entity import EntityId
from asseeibot.models.wikimedia.wikidata.item import Item


@dataclass
class NamedEntityRecognition:
    """This models the science subject ontology

    The ontology has ~34.000 Wikidata items
    The source of the ontology is YSO and library of congress classification
    and Wikidatas curated subgraph of academic disciplines:

    You can generate/download it here:
    https://query.wikidata.org/#%23Katter%0ASELECT%20DISTINCT%20%3Fitem%20%3FitemLabel%20%3Falias%20%3Fdescription%0AWHERE%20%0A%7B%0A%20%20%7B%0A%20%20%3Fitem%20wdt%3AP2347%20%5B%5D%20%23%20YSO%0A%20%20%7D%20union%20%7B%0A%20%20%3Fitem%20wdt%3AP1149%20%5B%5D%20%23%20LC%20classification%0A%20%20%20%20%20%20%20%20%7Dunion%20%7B%0A%20%20%3Fitem%20wdt%3AP31%2Fwdt%3AP279%2a%20wd%3AQ11862829%0A%20%20%20%20%20%20%20%20%7D%0A%20%20minus%7B%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ41298%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20optional%7B%0A%20%20%3Fitem%20skos%3AaltLabel%20%3Falias.%0A%20%20filter%28lang%28%3Falias%29%20%3D%20%22en%22%29%0A%20%20%20%3Fitem%20schema%3Adescription%20%3Fdescription.%0A%20%20filter%28lang%28%3Fdescription%29%20%3D%20%22en%22%29%0A%20%20%20%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%20%23%20Hj%C3%A4lper%20dig%20h%C3%A4mta%20etiketten%20p%C3%A5%20ditt%20spr%C3%A5k%2C%20om%20inte%20annat%20p%C3%A5%20engelska%0A%7D

    It takes a list of subjects and returns supervised 
    matches above a certain threshold if they are approved by the user.

    The threshold determines which matches to show to the user.
    The higher the closer the words are semantically calculated using
    https://en.wikipedia.org/wiki/Levenshtein_distance
    """
    raw_subjects: Optional[List[str]]
    subject_qids: Set[str] = None  # Got "TypeError: unhashable type: 'EntityId'" so we use a str for now
    dataframe: Any = None
    __alias_threshold: int = 85
    __label_threshold: int = 82

    class Config:
        arbitrary_types_allowed = True

    def __download_the_ontology_pickle(self):
        raise NotImplementedError

    def __post_init_post_parse__(self):
        if self.raw_subjects is not None:
            self.__prepare_the_dataframe__()
            self.__lookup_subjects__()

    def __prepare_the_dataframe__(self):
        # This pickle is ~3MB in size and takes less than a second to load.
        # noinspection PyUnresolvedReferences
        self.dataframe: Dataset["item", "itemLabel", "alias"] = pd.read_pickle("ontology.pkl")
        # This is needed for the fuzzymatching to work properly
        self.dataframe = self.dataframe.fillna('')

    def __lookup_in_ontology__(self, subject: str) -> Optional[FuzzyMatch]:
        """Looks up the subject in the ontology and triy to fuzzymatch it to a QID"""

        def extract_top_match_row():
            """Get the first row"""
            for row in self.dataframe.itertuples(index=False):
                # This is a NamedTuple
                return row

        def extract_top_match_score(column: DataFrameColumns) -> PositiveInt:
            if not (column == DataFrameColumns.ALIAS or column == DataFrameColumns.LABEL):
                raise ValueError("did not get a column we support")
            row = extract_top_match_row()
            if column == DataFrameColumns.LABEL:
                return row.label_score
            else:
                return row.alias_score

        def extract_top_matches():
            self.dataframe = self.dataframe.sort_values("label_score", ascending=False)
            label_score = extract_top_match_score(column=DataFrameColumns.LABEL)
            if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
                print_dataframe_head()
            top_label_match = get_top_match()
            self.dataframe = self.dataframe.sort_values("alias_score", ascending=False)
            alias_score = extract_top_match_score(column=DataFrameColumns.ALIAS)
            if config.loglevel == logging.INFO or config.loglevel == logging.DEBUG:
                print_dataframe_head()
            top_alias_match = get_top_match()
            return label_score, alias_score, top_label_match, top_alias_match

        def get_top_match():
            row = extract_top_match_row()
            # logger.debug(f"row:{row}")
            # present the match
            return FuzzyMatch(**dict(
                qid=EntityId(row.item),
                alias=row.alias,
                label=row.itemLabel,
                description=row.description
            ))

        def lookup_in_cache(subject: str):
            if subject is None or subject == "":
                return
            cache = Cache()
            qid = cache.read(label=subject)
            if qid is not None:
                logger.info("Already matched QID found in the cache")
                return FuzzyMatch(
                    qid=EntityId(raw_entity_id=qid)
                )

        def calculate_scores(subject: str):
            print(f"NER matching on '{subject}'")
            # This code is inspired by Nikhil VJ
            # https://stackoverflow.com/questions/38577332/apply-fuzzy-matching-across-a-dataframe-column-and-save-results-in-a-new-column
            self.dataframe["label_score"] = self.dataframe.itemLabel.apply(lambda x: fuzz.ratio(x, subject))
            self.dataframe["alias_score"] = self.dataframe.alias.apply(lambda x: fuzz.ratio(x, subject))
            # print(self.dataframe.head())

        def print_dataframe_head():
            print(self.dataframe.head(2))

        if not isinstance(subject, str):
            raise TypeError(f"subject was '{subject}' which is not a string")
        logger = logging.getLogger(__name__)
        subject = subject.strip()
        cache_match = lookup_in_cache(subject)
        if cache_match is not None:
            return cache_match
        calculate_scores(subject)
        label_score, alias_score, top_label_match, top_alias_match = extract_top_matches()
        if label_score >= alias_score:
            if label_score >= self.__label_threshold:
                answer = yes_no_question("Does this match?\n"
                                         f"{str(top_label_match)}")
                if answer:
                    cache_instance = Cache()
                    cache_instance.add(label=subject, qid=top_label_match.qid.value)
                    return top_label_match
        if alias_score >= self.__alias_threshold:
            answer = yes_no_question("Does this match?\n"
                                     f"{str(top_alias_match)}")
            if answer:
                cache_instance = Cache()
                cache_instance.add(label=subject, qid=top_alias_match.qid.value)
                return top_alias_match
        # None of the ratios reached the threshold
        # We probably have either a gap in our ontology or in Wikidata
        item = Item()
        logger.warning(f"No match with a sufficient rating found. "
                       f"Search for the subject on Wikidata: "
                       f"{item.string_search_url(string=subject)}")
        # exit()

    def __lookup_subjects__(self):
        def detect_comma_comma_and_formatting(subject: str):
            if subject is None or subject == "":
                raise ValueError
            regex = "^(?:(\w+)[, ]*)+and (\w+)$"
            match = re.search(regex, subject)
            raise NotImplementedError

        logger = logging.getLogger(__name__)
        self.subject_qids = set()
        for subject in self.raw_subjects:
            # detect_comma_comma_and_formatting(subject)
            result = self.__lookup_in_ontology__(subject)
            if result is not None:
                self.subject_qids.add(result.qid.value)
            else:
                logger.info("We try splitting the subject up along commas")
                split_subject_parts = subject.split(",")
                if len(split_subject_parts) > 1:
                    for split_subject in split_subject_parts:
                        result = self.__lookup_in_ontology__(split_subject)
                        if result is not None:
                            # print(result)
                            self.subject_qids.add(result.qid.value)
                logger.info("We try splitting the subject up along 'and'")
                split_subject_parts = subject.split(" and ")
                if len(split_subject_parts) > 1:
                    for split_subject in split_subject_parts:
                        result = self.__lookup_in_ontology__(split_subject)
                        if result is not None:
                            # print(result)
                            self.subject_qids.add(result.qid.value)
                # print("debug split exit")
                # exit()
            # if result is not None:
            #     pprint(result)
            # print("debug exit")
            # exit()
