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
    """These are special to our ontology"""
    ALIAS = "alias"
    DESCRIPTION = "description"
    ITEM = "item"
    LABEL = "itemLabel"
