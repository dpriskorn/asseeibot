from enum import Enum


class WikimediaSite(Enum):
    WIKIPEDIA = "wikipedia"


class WikimediaEditType(Enum):
    NEW = "new"
    EDIT = "edit"
    LOG = "log"