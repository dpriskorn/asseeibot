import logging
from typing import List

from pydantic import BaseModel

from asseeibot.models.crossref.enums import SupportedSplit
from asseeibot.models.enums import MatchStatus
from asseeibot.models.ontology import Ontology
from asseeibot.models.ontology_dataframe import OntologyDataframeSetup

logger = logging.getLogger(__name__)


class CrossrefSubject(BaseModel):
    """This class handles all the splitting and lookup of a single original subject from Crossref"""
    original_subject: str
    subject: str = None
    match_status: MatchStatus = None
    ontology: Ontology = None

    class Config:
        arbitrary_types_allowed = True

    def __lookup_in_ontology__(self,
                               subject: str = None,
                               split_subject: bool = False):
        """This perform one lookup and update the match_status"""
        if subject is None:
            raise ValueError("subject was None")
        self.ontology = Ontology(crossref_subject=subject,
                                 original_subject=self.original_subject,
                                 split_subject=split_subject)
        self.ontology.lookup_subject()
        if self.ontology.match is not None:
            if self.ontology.match == MatchStatus.APPROVED:
                logger.info("This subject was approved")
                self.match_status = MatchStatus.APPROVED
            else:
                self.match_status = MatchStatus.DECLINED
                logger.info("This subject was declined earlier so we skip it")
        else:
            logger.info("Got no match from the ontology")
            self.match_status = MatchStatus.NO_MATCH

    def __lookup_after_split__(self, split_subject_parts: List[str]):
        """This looks up split subjects"""
        if split_subject_parts is None:
            raise ValueError("split_subject_parts was None")
        if len(split_subject_parts) > 1:
            for split_subject in split_subject_parts:
                split_subject = split_subject.strip()
                self.__lookup_in_ontology__(split_subject,
                                            split_subject=True)

    def __split__(self, supported_split: SupportedSplit):
        if supported_split is None:
            raise ValueError("supported_split was None")
        if supported_split == SupportedSplit.COMMA:
            logger.info("We try splitting the subject up along commas")
            return self.original_subject.split(",")
        elif supported_split == SupportedSplit.AND:
            logger.info("We try splitting the subject up along 'and'")
            return self.original_subject.split(" and ")

    def __split_subject_and_lookup__(self):
        logger.info("We got no match, so we now try splitting it up "
                    "and see if the parts make any sense")
        # TODO combine also the first, x, x parts with the last e.g in
        self.__lookup_after_split__(self.__split__(SupportedSplit.COMMA))
        self.__lookup_after_split__(self.__split__(SupportedSplit.AND))

    def __strip_original_subject__(self):
        self.original_subject = self.original_subject.strip()

    def lookup(self):
        """This function splits the subject string
        if no approved or declined match on the whole string is found"""
        self.__strip_original_subject__()
        # detect_comma_comma_and_formatting(subject)
        self.__lookup_in_ontology__(subject=self.original_subject,
                                    split_subject=False)
        # We only proceed if it has not been approved/declined before
        # because we don't want to spam the user with the same
        # question over and over.
        if self.match_status == MatchStatus.NO_MATCH:
            self.__split_subject_and_lookup__()
        else:
            logger.info(f"This subject has already been {MatchStatus.name.lower()}")

    # def detect_comma_comma_and_formatting(subject: str):
    #     if subject is None or subject == "":
    #         raise ValueError
    #     regex = "^(?:(\w+)[, ]*)+and (\w+)$"
    #     match = re.search(regex, subject)
    #     raise NotImplementedError
