from enum import Enum


class CrossrefEntryType(Enum):
    BOOK = "book"
    BOOK_CHAPTER = "book-chapter"
    COMPONENT = "component"
    JOURNAL_ARTICLE = "journal-article"
    PROCEEDINGS_ARTICLE = "proceedings-article"
    REFERENCE_ENTRY = "reference-entry"
    REPORT = "report"


class CrossrefContentType(Enum):
    UNSPECIFIED = "unspecified"
    HTML = "text/html"
    PDF = "application/pdf"
    TEXT_XML = "text/xml"
    XML = "application/xml"
    PLAIN_TEXT = "text/plain"


class SupportedSplit(Enum):
    COMMA = ","
    AND = " and "
