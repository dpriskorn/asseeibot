from enum import Enum, auto


class MatchStatus(Enum):
    """Models the 3 states of matching approved/declined/no_match
    The 2 former are stored in our MatchCache in a boolean.

    We could used a variable with True/False/None but
    this makes the code way more readable"""
    APPROVED = auto()
    DECLINED = auto()
    NO_MATCH = auto()


class PywikibotSite(Enum):
    WIKIPEDIA = "wikipedia"


class OntologyDataframeColumn(Enum):
    """These are special to our ontology, but they are standard names in WDQS"""
    ALIAS = "alias"
    DESCRIPTION = "description"
    ITEM = "item"
    LABEL = "label"
    LABEL_SCORE = "label_score"
    ALIAS_SCORE = "alias_score"


class MatchBasedOn(Enum):
    LABEL = "label"
    ALIAS = "alias"


class CacheDataframeColumn(Enum):
    QID = "qid"
    CROSSREF_SUBJECT = "crossref_subject"
    MATCH_BASED_ON = "match_based_on"
    SPLIT_SUBJECT = "split_subject"
    ORIGINAL_SUBJECT = "original_subject"
    APPROVED = "approved"


class StatisticDataframeColumn(Enum):
    EDITED_QID = "edited_qid"
    SUBJECT_QID = "subject_qid"
    CROSSREF_SUBJECT = "crossref_subject"
    MATCH_BASED_ON = "match_based_on"
    SPLIT_SUBJECT = "split_subject"
    ORIGINAL_SUBJECT = "original_subject"
    DATETIME = "datetime"
    ROLLED_BACK = "rolled_back"
