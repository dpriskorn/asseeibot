from enum import Enum


class WikimediaSite(Enum):
    WIKIPEDIA = "wikipedia"


class WikimediaEditType(Enum):
    NEW = "new"
    EDIT = "edit"
    LOG = "log"
    CATEGORIZE = "categorize"
    UNKNOWN = "142"


class WikidataNamespaceLetters(Enum):
    PROPERTY = "P"
    ITEM = "Q"
    LEXEME = "L"
    # FORM = "F"
    # SENSE = "S"


class DataFrameColumns(Enum):
    """These are special to our ontology, but they are standard names in WDQS"""
    ALIAS = "alias"
    DESCRIPTION = "description"
    ITEM = "item"
    LABEL = "itemLabel"


class StatedIn(Enum):
    CROSSREF = "Q5188229"


class DeterminationMethod(Enum):
    FUZZY_POWERED_NAMED_ENTITY_RECOGNITION_MATCHER = "Q110733873"


class Property(Enum):
    MAIN_SUBJECT = "P921"
    DETERMINATION_METHOD = "P459"
