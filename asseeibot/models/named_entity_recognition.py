import logging
from enum import Enum
from typing import Optional, List

from pandas import DataFrame
from pydantic import BaseModel

from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.ontology import Ontology
from asseeibot.models.ontology_dataframe import Dataframe


class SupportedSplit(Enum):
    COMMA = ","
    AND = " and "


class NamedEntityRecognition(BaseModel):
    """This models the science subject ontology

    It takes a list of subjects and returns supervised
    matches above a certain threshold if they are approved by the user.

    The threshold determines which matches to show to the user.
    The higher the closer the words are semantically calculated using
    https://en.wikipedia.org/wiki/Levenshtein_distance
    """
    raw_subjects: Optional[List[str]]
    ontology: Ontology = None
    already_matched_qids: List[str] = None
    __dataframe: DataFrame = None
    subject_matches: List[FuzzyMatch] = None
    match_found: bool = None

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        if self.raw_subjects is not None:
            dataframe = Dataframe()
            dataframe.prepare_the_dataframe()
            self.__lookup_subjects__()

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

        def lookup(subject, original_subject, split_subject: bool):
            """This perform one lookup and append to our lists if we find a match"""
            self.ontology = Ontology(crossref_subject=subject,
                                     original_subject=original_subject,
                                     dataframe=self.__dataframe,
                                     split_subject=split_subject)
            self.ontology.lookup_subject()
            if (
                    self.ontology.match is not None and
                    self.ontology.match.qid.value not in self.already_matched_qids
            ):
                self.subject_matches.append(self.ontology.match)
                self.already_matched_qids.append(self.ontology.match.qid.value)
                self.match_found = True
            else:
                self.match_found = False

        def lookup_after_split(split_subject_parts, original_subject):
            """This looks up split subjects"""
            if len(split_subject_parts) > 1:
                for split_subject in split_subject_parts:
                    split_subject = split_subject.strip()
                    lookup(split_subject,
                           original_subject,
                           split_subject=True)

        logger = logging.getLogger(__name__)
        self.already_matched_qids = []
        self.subject_matches = []
        for original_subject in self.raw_subjects:
            original_subject = original_subject.strip()
            # detect_comma_comma_and_formatting(subject)
            lookup(subject=original_subject,
                   original_subject=original_subject,
                   split_subject=False)
            if not self.match_found:
                logger.info("We did not find a match on the whole string.")
                lookup_after_split(split(SupportedSplit.COMMA, original_subject),
                                   original_subject)
                lookup_after_split(split(SupportedSplit.AND,
                                         original_subject),
                                   original_subject)
