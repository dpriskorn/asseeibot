#!/usr/bin/env python3
import logging
from datetime import datetime
from pprint import pprint
from typing import List, Dict, Any, TYPE_CHECKING, Set

from habanero import Crossref  # type: ignore
from purl import URL
from pydantic import BaseModel
from rich import print

from asseeibot.helpers import util
from asseeibot.models.crossref_enums import CrossrefEntryType
from asseeibot.models.identifiers.isbn import Isbn
from asseeibot.models.named_entity_recognition import NamedEntityRecognition
from asseeibot.models.wikimedia.wikidata_entity import EntityId


class CrossrefWork(BaseModel):
    doi: Any
    data: Dict[str, Any] = None
    author: str = None
    is_referenced_by_count: int = None
    isbn: Isbn = None
    issn: List[str] = None
    issn_qid: str = None
    issued: datetime = None
    license_qid: str = None
    license_url: str = None
    link: URL = None
    object_type: CrossrefEntryType = None
    original_title: str = None
    pdf_urls: List[str] = None
    publisher: str = None
    publisher_location: str = None
    raw_links: List[str] = None
    references: List = None
    references_count: int = None
    score: str = None
    raw_subjects: List[str] = None
    subject_qids: Set[EntityId] = None
    subtitle: str = None
    title: str = None
    url: URL = None
    xml_urls: List[str] = None

    class Config:
        arbitrary_types_allowed = True

    def __match_subjects_to_qids__(self):
        ner = NamedEntityRecognition(self.raw_subjects)
        self.subject_qids = ner.subject_qids

    def __parse__(self):
        logger = logging.getLogger(__name__)
        if self.data is None:
            raise ValueError("data was None")
        # Extract data
        for key, value in self.data.items():
            if key == "is-referenced-by-count":
                self.is_referenced_by_count = value
            elif key == "ISBN":
                self.isbn = Isbn(value=value)
            elif key == "ISSN":
                self.issn = value
                # TODO lookup ISSN using hub.toolforge.org like Houcemeddine?
                # if config.lookup_issn:
                #     qid = wikidata.lookup_issn(self.issn)
                #     if qid is not None:
                #         self.issn_qid = qid
            elif key == "published":
                if "date-parts" in value:
                    date_parts = value["date-parts"]
                    if len(date_parts) == 2:
                        # Assuming [%Y,%m]
                        self.issued = datetime(year=date_parts[0],
                                               month=date_parts[1])
                else:
                    pprint(value)
                    raise ValueError("this length of date parts is not supported yet")
                    # self.issued = datetime(value)
            elif key == "publisher-location":
                self.publisher_location = value
            elif key == "publisher":
                self.publisher = value
            elif key == "references-count":
                self.references_count = int(value)
            elif key == "URL":
                # This is the DOI url to the resolver.
                self.url = value
            elif key == "link":
                # This is fulltext links
                urls = None
                self.raw_links: Dict = self.data["link"]
                # Disabled for now
                # self.__parse_links__()
            elif key == "reference":
                self.references: List[Dict[str, str]] = value
            elif key == "license":
                # TODO detect garbage license URLs like
                # www.springer.com/tdm
                self.license_url = value
                if self.license_url is None:
                    logger.info("No license found for this article")
            elif key == "subject":
                self.raw_subjects = value
            else:
                logger.info(f"Skipping key: {key} with data: {value}")

    def __parse_links__(self) -> None:
        """Parses the links into attributes"""
        logger = logging.getLogger(__name__)
        if self.raw_links is not None:
            # TODO make this async
            # Link is a field in the Crossref metadata
            # refactor pseudo code
            # first get the file ending
            # then call a checker
            # then add to list if True
            supported_endings = ["pdf", "xml"]
            found = False
            self.pdf_urls = []
            self.xml_urls = []
            for link in self.raw_links:
                url = link["URL"]
                ending = url.split(".")[-1]
                print(f"ending:{ending}")
                pdf_duplicate = False
                xml_duplicate = False
                # Check for duplicates
                if len(self.pdf_urls) > 0 or len(self.xml_urls) > 0:
                    for pdf_url in self.pdf_urls:
                        if pdf_url == url:
                            pdf_duplicate = True
                            continue
                    for xml_url in self.xml_urls:
                        if xml_url == url:
                            xml_duplicate = True
                            continue
                if pdf_duplicate or xml_duplicate:
                    continue
                if ending == "pdf":
                    r = util.get_response(url)
                    if r is not False and util.check_if_pdf(r):
                        found = True
                        self.pdf_urls.append(url)
                    else:
                        continue
                if ending == "xml":
                    r = util.get_response(url)
                    if r is not False and util.check_if_xml(r):
                        found = True
                        self.xml_urls.append(url)
                    else:
                        continue
                if ending not in supported_endings:
                    print(f"URL ending not recognized: {link}")
                    # Test to see if it serves PDF or XML anyway
                    r = util.get_response(url)
                    if r is not False:
                        if util.check_if_pdf(r):
                            found = True
                            self.pdf_urls.append(url)
                        elif util.check_if_xml(r):
                            found = True
                            self.xml_urls.append(url)
                    else:
                        continue
            if found is False:
                logger.info("No fulltext links found")

    def __str__(self):
        return f"<{self.doi.value} {self.title}>"

    # def handle_references(
    #         references: List[Dict[str, str]],
    # ):
    #     """Handles references and look up any DOIs found"""
    #     # print(references)
    #     # if not in_wikipedia:
    #     #     print("Skipping adding references since this DOI was not found in "+
    #     #           "any Wikipedia yet")
    #     # else:
    #     print("First we add all the references of the DOI found i Wikipedia " +
    #           "so we can link to it.")
    #     dois = []
    #     for ref in references:
    #         key = ref["key"]
    #         if ref.get("DOI"):
    #             doi = ref["DOI"]
    #             if doi is not None:
    #                 dois.append(doi)
    #         else:
    #             print(f"DOI missing for key:{key}")
    #     if len(dois) > 0:
    #         wikidata.lookup_dois(dois)

    # # TODO implement caching to disk
    # def __call_wbi_search_entities__(self, subject):
    #     return search_entities(search_string=subject,
    #                                  language="en",
    #                                  dict_result=True,
    #                                  max_results=1)

