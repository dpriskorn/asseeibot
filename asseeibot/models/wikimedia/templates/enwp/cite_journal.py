import logging
from typing import Optional

from asseeibot.models.identifiers.doi import Doi
from asseeibot.models.wikimedia.wikipedia_page_reference import WikipediaPageReference


class CiteJournal(WikipediaPageReference):
    """This models the template cite journal in English Wikipedia"""
    doi: Optional[Doi]
    title: str = None
    journal_title: str = None
    jstor: str = None
    pmid: str = None
    scopus_id: str = None

    def __post_init_post_parse__(self):
        logger = logging.getLogger(__name__)
        # Convert after pydantic finished parsing
        # because it cannot parse into a Doi when given a string.
        self.doi: Doi = Doi(self.doi)
        logger.info("post init post parse was run")

    # def __parse_template__(self):
    #     logger = logging.getLogger(__name__)
    #     for key, value in self.content.items():
    #         if key == "doi":
    #             logger.info(f"Found doi: {value}")
    #             self.doi = Doi(value)
    #         if key == "journal_title":
    #             logger.info(f"Found journal_title: {value}")
    #             # Todo decide about how to handle the [[]] of this value
    #             # Could we get the QID for the journal_title?
    #             self.journal_title = value
    #         if key == "jstor":
    #             logger.info(f"Found jstor: {value}")
    #             self.jstor = value
    #         if key == "pmid":
    #             logger.info(f"Found pmid: {value}")
    #             self.pmid = value
    #         if key == "title":
    #             logger.info(f"Found title: {value}")
    #             self.article_title = value

    def __str__(self):
        return f"<{self.title} (doi:{self.doi} pmid:{self.pmid} jstor:{self.jstor})>"
