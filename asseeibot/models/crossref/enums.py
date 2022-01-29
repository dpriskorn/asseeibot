from enum import Enum


class CrossrefEntryType(Enum):
    BOOK = "book"
    JOURNAL_ARTICLE = "journal-article"
    PROCEEDINGS_ARTICLE = "proceedings-article"
    BOOK_CHAPTER = "book-chapter"
    COMPONENT = "component"


class CrossrefContentType(Enum):
    UNSPECIFIED = "unspecified"
    HTML = "text/html"
    PDF = "application/pdf"
    TEXT_XML = "text/xml"
    XML = "application/xml"
    PLAIN_TEXT = "text/plain"
