import logging
from typing import OrderedDict


class CiteJournal:
    journal: str = None
    doi: str = None
    jstor: str = None
    pmid: str = None
    article_title: str = None
    scopus_id: str = None

    def __init__(self,
                 content: OrderedDict[str, str]):
        logger = logging.getLogger(__name__)
        for key, value in content.items():
            if key == "doi":
                logger.info(f"Found doi: {value}")
                self.doi = value
            if key == "journal":
                logger.info(f"Found journal: {value}")
                self.journal = value
            if key == "jstor":
                logger.info(f"Found jstor: {value}")
                self.jstor = value
            if key == "pmid":
                logger.info(f"Found pmid: {value}")
                self.pmid = value
            if key == "title":
                logger.info(f"Found title: {value}")
                self.article_title = value

    def __str__(self):
        return f"<{self.article_title} (doi:{self.doi} pmid:{self.pmid} jstor:{self.jstor})>"