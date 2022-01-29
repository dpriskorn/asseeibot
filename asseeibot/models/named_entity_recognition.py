import logging
from enum import Enum
from typing import Optional, List, Any

import pandas as pd
from dataenforce import Dataset
from pydantic.dataclasses import dataclass

import config
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.ontology import Ontology


class SupportedSplit(Enum):
    COMMA = ","
    AND = " and "


@dataclass
class NamedEntityRecognition:
    """This models the science subject ontology

    It takes a list of subjects and returns supervised
    matches above a certain threshold if they are approved by the user.

    The threshold determines which matches to show to the user.
    The higher the closer the words are semantically calculated using
    https://en.wikipedia.org/wiki/Levenshtein_distance

    Version 3 of the ontology has ~26k Wikidata items out of which ~23k
    have a description and ~13k have at least one alias

    The source of the ontology is YSO and library of congress classification
    and Wikidatas curated subgraph of academic disciplines:

    You can generate/download it here:
    first version
    https://query.wikidata.org/#%23Katter%0ASELECT%20DISTINCT%20%3Fitem%20%3FitemLabel%20%3Falias%20%3Fdescription%0AWHERE%20%0A%7B%0A%20%20%7B%0A%20%20%3Fitem%20wdt%3AP2347%20%5B%5D%20%23%20YSO%0A%20%20%7D%20union%20%7B%0A%20%20%3Fitem%20wdt%3AP1149%20%5B%5D%20%23%20LC%20classification%0A%20%20%20%20%20%20%20%20%7Dunion%20%7B%0A%20%20%3Fitem%20wdt%3AP31%2Fwdt%3AP279%2a%20wd%3AQ11862829%0A%20%20%20%20%20%20%20%20%7D%0A%20%20minus%7B%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ41298%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20optional%7B%0A%20%20%3Fitem%20skos%3AaltLabel%20%3Falias.%0A%20%20filter%28lang%28%3Falias%29%20%3D%20%22en%22%29%0A%20%20%20%3Fitem%20schema%3Adescription%20%3Fdescription.%0A%20%20filter%28lang%28%3Fdescription%29%20%3D%20%22en%22%29%0A%20%20%20%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%20%23%20Hj%C3%A4lper%20dig%20h%C3%A4mta%20etiketten%20p%C3%A5%20ditt%20spr%C3%A5k%2C%20om%20inte%20annat%20p%C3%A5%20engelska%0A%7D
    second improved version with branches of science also
    https://query.wikidata.org/#%23%20Domain%20specific%20ontology%20for%20asseeibots%20fuzzy-powered%20NER-matcher%0ASELECT%20DISTINCT%20%3Fitem%20%3FitemLabel%20%3Falias%20%3Fdescription%0AWHERE%20%0A%7B%0A%20%20%7B%0A%20%20%3Fitem%20wdt%3AP2347%20%5B%5D%20%23%20YSO%0A%20%20%7D%20union%20%7B%0A%20%20%3Fitem%20wdt%3AP1149%20%5B%5D%20%23%20LC%20classification%0A%20%20%20%20%20%20%20%20%7Dunion%20%7B%0A%20%20values%20%3Fvalues%20%7B%0A%20%20%20%20wd%3AQ2465832%20%23%20branch%20of%20science%0A%20%20%20%20wd%3AQ11862829%20%23%20academic%20discipline%0A%20%20%7D%0A%20%20%3Fitem%20wdt%3AP31%2Fwdt%3AP279%2a%20%3Fvalues.%0A%20%20%20%20%20%20%20%20%7D%0A%20%20minus%7B%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ41298%20%23%20journal%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20optional%7B%0A%20%20%3Fitem%20skos%3AaltLabel%20%3Falias.%0A%20%20filter%28lang%28%3Falias%29%20%3D%20%22en%22%29%0A%20%20%3Fitem%20schema%3Adescription%20%3Fdescription.%0A%20%20filter%28lang%28%3Fdescription%29%20%3D%20%22en%22%29%0A%20%20%20%20%7D%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%20%23%20Hj%C3%A4lper%20dig%20h%C3%A4mta%20etiketten%20p%C3%A5%20ditt%20spr%C3%A5k%2C%20om%20inte%20annat%20p%C3%A5%20engelska%0A%7D
    version 3
    2 queries for this because of a bug in WDQS
    query with items missing english description:
    https://query.wikidata.org/#%23%20Domain%20specific%20ontology%20for%20asseeibots%20fuzzy-powered%20NER-matcher%0ASELECT%20DISTINCT%20%3Fitem%20%3Flabel%20%3Falias%20%3Fdescription%0AWHERE%20%0A%7B%0A%20%20%7B%0A%20%20%3Fitem%20wdt%3AP2347%20%5B%5D%20%23%20YSO%0A%20%20%7D%20union%20%7B%0A%20%20%3Fitem%20wdt%3AP1149%20%5B%5D%20%23%20LC%20classification%0A%20%20%20%20%20%20%20%20%7Dunion%20%7B%0A%20%20values%20%3Fvalues%20%7B%0A%20%20%20%20wd%3AQ2465832%20%23%20branch%20of%20science%0A%20%20%20%20wd%3AQ11862829%20%23%20academic%20discipline%0A%20%20%7D%0A%20%20%3Fitem%20wdt%3AP31%2Fwdt%3AP279%2a%20%3Fvalues.%0A%20%20%20%20%20%20%20%20%7D%0A%20%20minus%7B%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ41298%20%23%20journal%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20optional%7B%0A%20%20%3Fitem%20skos%3AaltLabel%20%3Falias.%0A%20%20filter%28lang%28%3Falias%29%20%3D%20%22en%22%29%0A%20%20%20%20%7D%0A%20%20%23filter%20not%20exists%7B%0A%20%20%3Fitem%20rdfs%3Alabel%20%3Flabel.%0A%20%20filter%28lang%28%3Flabel%29%20%3D%20%22en%22%29%0A%20%20%23%7D%0A%20%20filter%20not%20exists%7B%0A%20%20%3Fitem%20schema%3Adescription%20%3Fdescription.%0A%20%20filter%28lang%28%3Fdescription%29%20%3D%20%22en%22%29%0A%20%20%7D%0A%7D%0Aoffset%200%0A%23limit%2020
    query with items that have both label and description:
    https://query.wikidata.org/#%23%20Domain%20specific%20ontology%20for%20asseeibots%20fuzzy-powered%20NER-matcher%0ASELECT%20DISTINCT%20%3Fitem%20%3Flabel%20%3Falias%20%3Fdescription%0AWHERE%20%0A%7B%0A%20%20%7B%0A%20%20%3Fitem%20wdt%3AP2347%20%5B%5D%20%23%20YSO%0A%20%20%7D%20union%20%7B%0A%20%20%3Fitem%20wdt%3AP1149%20%5B%5D%20%23%20LC%20classification%0A%20%20%20%20%20%20%20%20%7Dunion%20%7B%0A%20%20values%20%3Fvalues%20%7B%0A%20%20%20%20wd%3AQ2465832%20%23%20branch%20of%20science%0A%20%20%20%20wd%3AQ11862829%20%23%20academic%20discipline%0A%20%20%7D%0A%20%20%3Fitem%20wdt%3AP31%2Fwdt%3AP279%2a%20%3Fvalues.%0A%20%20%20%20%20%20%20%20%7D%0A%20%20minus%7B%0A%20%20%20%20%3Fitem%20wdt%3AP31%20wd%3AQ41298%20%23%20journal%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20optional%7B%0A%20%20%3Fitem%20skos%3AaltLabel%20%3Falias.%0A%20%20filter%28lang%28%3Falias%29%20%3D%20%22en%22%29%0A%20%20%20%20%7D%0A%20%20%23filter%20not%20exists%7B%0A%20%20%3Fitem%20rdfs%3Alabel%20%3Flabel.%0A%20%20filter%28lang%28%3Flabel%29%20%3D%20%22en%22%29%0A%20%20%23%7D%0A%20%20%23filter%20not%20exists%7B%0A%20%20%3Fitem%20schema%3Adescription%20%3Fdescription.%0A%20%20filter%28lang%28%3Fdescription%29%20%3D%20%22en%22%29%0A%20%20%23%7D%0A%7D%0Aoffset%200%0A%23limit%2020
    """
    raw_subjects: Optional[List[str]]
    __ontology: Ontology = None
    __already_matched_qids: List[str] = None
    subject_matches: List[FuzzyMatch] = None
    __dataframe: Any = None

    class Config:
        arbitrary_types_allowed = True

    def __download_the_ontology_pickle(self):
        raise NotImplementedError

    def __post_init_post_parse__(self):
        if self.raw_subjects is not None:
            self.__prepare_the_dataframe__()
            self.__lookup_subjects__()

    @staticmethod
    def __prepare_the_dataframe__():
        if config.ontology_dataframe is None:
            # This pickle is ~4MB in size and takes less than a second to load.
            # noinspection PyUnresolvedReferences
            dataframe: Dataset["item", "itemLabel", "alias"] = pd.read_pickle("ontology.pkl")
            # This is needed for the fuzzymatching to work properly
            config.ontology_dataframe = dataframe.fillna('')

    def __lookup_subjects__(self):
        """This function splits the subject string
        if no match on the whole string is found"""

        # def detect_comma_comma_and_formatting(subject: str):
        #     if subject is None or subject == "":
        #         raise ValueError
        #     regex = "^(?:(\w+)[, ]*)+and (\w+)$"
        #     match = re.search(regex, subject)
        #     raise NotImplementedError

        def split(supported_split, original_subject):
            if supported_split == SupportedSplit.COMMA:
                logger.info("We try splitting the subject up along commas")
                return original_subject.split(",")
            elif supported_split == SupportedSplit.AND:
                logger.info("We try splitting the subject up along 'and'")
                return original_subject.split(" and ")

        def lookup(subject, original_subject):
            """This perform one lookup and append to our lists if we find a match"""
            self.ontology = Ontology(subject=subject,
                                     original_subject=original_subject,
                                     dataframe=self.__dataframe)
            match = self.ontology.lookup_subject()
            if match is not None and match.qid.value not in self.__already_matched_qids:
                self.subject_matches.append(match)
                self.__already_matched_qids.append(match.qid.value)

        def lookup_after_split(split_subject_parts, original_subject):
            """This looks up split subjects"""
            if len(split_subject_parts) > 1:
                for split_subject in split_subject_parts:
                    split_subject = split_subject.strip()
                    lookup(split_subject, original_subject)

        logger = logging.getLogger(__name__)
        self.__already_matched_qids = []
        self.subject_matches = []
        for original_subject in self.raw_subjects:
            original_subject = original_subject.strip()
            # detect_comma_comma_and_formatting(subject)
            lookup(subject=original_subject, original_subject=original_subject)
            if self.__already_matched_qids != 1:
                # We did not find a match on the whole string. Lets split it!
                lookup_after_split(split(SupportedSplit.COMMA, original_subject), original_subject)
                lookup_after_split(split(SupportedSplit.AND, original_subject), original_subject)
