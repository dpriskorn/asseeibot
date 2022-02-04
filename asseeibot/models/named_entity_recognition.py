import logging
from typing import Optional, List

from pydantic import BaseModel

from asseeibot.models.crossref.subject import CrossrefSubject
from asseeibot.models.enums import MatchStatus
from asseeibot.models.fuzzy_match import FuzzyMatch

logger = logging.getLogger(__name__)


class NamedEntityRecognition(BaseModel):
    """This models the science subject ontology

    It takes a list of subjects and returns supervised
    matches above a certain threshold if they are approved by the user.

    The threshold determines which matches to show to the user.
    The higher the closer the words are semantically calculated using
    https://en.wikipedia.org/wiki/Levenshtein_distance
    """
    raw_subjects: Optional[List[str]]
    already_matched_qids: List[str] = None
    subject_matches: List[FuzzyMatch] = None

    def __lookup_subjects__(self):
        self.already_matched_qids = []
        self.subject_matches = []
        for original_subject in self.raw_subjects:
            crossref_subject = CrossrefSubject(original_subject=original_subject)
            crossref_subject.lookup()
            if crossref_subject.match_status == MatchStatus.APPROVED:
                logger.debug("Adding approved match to the list of matches")
                if crossref_subject.ontology.match is None:
                    raise ValueError("crossref_subject.ontology.match was wrong")
                self.subject_matches.append(crossref_subject.ontology.match)
                self.already_matched_qids.append(crossref_subject.ontology.match.qid.value)
            elif crossref_subject.match_status == MatchStatus.DECLINED:
                logger.debug("Ignoring declined match.")
                # input("press enter")
            else:
                logger.debug("No match")
                 # input("press enter")

    def start(self):
        if self.raw_subjects is not None:
            self.__lookup_subjects__()
