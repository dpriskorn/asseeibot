#!/usr/bin/env python3
from datetime import datetime
from typing import List, Any, Set, Optional, Union

from habanero import Crossref  # type: ignore
from pydantic import BaseModel, PositiveInt, conint

from asseeibot.models.crossref_enums import CrossrefEntryType, CrossrefContentType
from asseeibot.models.identifiers.isbn import Isbn
from asseeibot.models.named_entity_recognition import NamedEntityRecognition


class OrdinalWordToIntegerConverter(BaseModel):
    word: str
    words = ["first", "second"]

    def get_integer(self):
        if self.word in self.words:
            for index, value in enumerate(self.words):
                if value == self.word:
                    # Python lists are zero indexed so we +1 here
                    return index + 1
        else:
            raise ValueError(f"{self.word} is not supported")


class CrossrefAuthor(BaseModel):
    given: Optional[str]
    family: Optional[str]
    sequence: Optional[str]
    affiliation: Optional[List[Any]]


class CrossrefDateParts(BaseModel):
    date_parts: Optional[List[List[conint(ge=0, lt=2023)]]]
    date_time: Optional[datetime]


class CrossrefLink(BaseModel):
    url: str
    content_type: Optional[CrossrefContentType]
    intended_application: Optional[str]


class CrossrefReference(BaseModel):
    key: Optional[str]
    # doi-asserted-by
    first_page: Optional[Union[PositiveInt, str]]
    doi: Optional[str]
    article_title: Optional[str]
    volume: Optional[str]  # This is often a PositiveInt but str like "Volume 8" do appear
    author: Optional[str]
    year: Optional[Union[conint(gt=1800, lt=2023), str]]  # can be a string like "2002a"
    journal_tile: Optional[str]


class CrossrefWork(BaseModel):
    author: Optional[List[CrossrefAuthor]]
    doi: Any  # typing it here does not work. We get an ugly " not yet prepared so type is still a ForwardRef" error
    is_referenced_by_count: Optional[conint(ge=0)]
    __isbn: Optional[List[str]]
    issn: Optional[List[str]]
    issn_qid: Optional[str]
    issued: Optional[CrossrefDateParts]
    __license_url: Optional[str]
    link: Optional[List[CrossrefLink]]
    object_type: Optional[CrossrefEntryType]
    original_title: Optional[List[str]]
    pdf_urls: Optional[List[str]]
    prefix: Optional[str]
    published: Optional[CrossrefDateParts]
    published_print: Optional[CrossrefDateParts]
    publisher: Optional[str]
    publisher_location: Optional[str]
    reference: Optional[List[CrossrefReference]]
    references_count: Optional[conint(ge=0)]
    score: str
    subject: Optional[List[str]]  # raw subjects
    subject_qids: Optional[Set[str]]
    source: str
    subtitle: Optional[List[str]]
    title: Optional[List[Any]]
    # url: str
    xml_urls: Optional[List[str]]

    class Config:
        arbitrary_types_allowed = True

    def parse_into_objects(self):
        # now we got the messy data from CrossRef
        pass

    def match_subjects_to_qids(self):
        if self.subject is not None:
            ner = NamedEntityRecognition(raw_subjects=self.subject)
            self.subject_qids = ner.subject_qids

    # def __parse_links__(self) -> None:
    #     """Parses the links into attributes"""
    #     logger = logging.getLogger(__name__)
    #     if self.raw_links is not None:
    #         # TODO make this async
    #         # Link is a field in the Crossref metadata
    #         # refactor pseudo code
    #         # first get the file ending
    #         # then call a checker
    #         # then add to list if True
    #         supported_endings = ["pdf", "xml"]
    #         found = False
    #         self.pdf_urls = []
    #         self.xml_urls = []
    #         for link in self.raw_links:
    #             url = link["url"]
    #             ending = url.split(".")[-1]
    #             print(f"ending:{ending}")
    #             pdf_duplicate = False
    #             xml_duplicate = False
    #             # Check for duplicates
    #             if len(self.pdf_urls) > 0 or len(self.xml_urls) > 0:
    #                 for pdf_url in self.pdf_urls:
    #                     if pdf_url == url:
    #                         pdf_duplicate = True
    #                         continue
    #                 for xml_url in self.xml_urls:
    #                     if xml_url == url:
    #                         xml_duplicate = True
    #                         continue
    #             if pdf_duplicate or xml_duplicate:
    #                 continue
    #             if ending == "pdf":
    #                 r = util.get_response(url)
    #                 if r is not False and util.check_if_pdf(r):
    #                     found = True
    #                     self.pdf_urls.append(url)
    #                 else:
    #                     continue
    #             if ending == "xml":
    #                 r = util.get_response(url)
    #                 if r is not False and util.check_if_xml(r):
    #                     found = True
    #                     self.xml_urls.append(url)
    #                 else:
    #                     continue
    #             if ending not in supported_endings:
    #                 print(f"URL ending not recognized: {link}")
    #                 # Test to see if it serves PDF or XML anyway
    #                 r = util.get_response(url)
    #                 if r is not False:
    #                     if util.check_if_pdf(r):
    #                         found = True
    #                         self.pdf_urls.append(url)
    #                     elif util.check_if_xml(r):
    #                         found = True
    #                         self.xml_urls.append(url)
    #                 else:
    #                     continue
    #         if found is False:
    #             logger.info("No fulltext links found")

    def __str__(self):
        return f"<{self.doi} {self.title[0]}>"

    @property
    def isbn_list(self):
        isbns = []
        for isbn in self.__isbn:
            isbns.append(Isbn(value=isbn))
        return isbns

    @property
    def license_qid(self):
        raise NotImplementedError("resolve the license url before returning")

    @property
    def number_of_subject_qids(self):
        return len(self.subject_qids)

    @property
    def references(self):
        return self.reference
        # raise NotImplementedError("resolve the license url before returning")

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

    # def __parse__(self):
    #     logger = logging.getLogger(__name__)
    #     if self.data is None:
    #         raise ValueError("data was None")
    #     # Extract data
    #     for key, value in self.data.items():
    #         if key == "is-referenced-by-count":
    #             self.is_referenced_by_count = value
    #         elif key == "ISBN":
    #             self.__isbn = Isbn(value=value)
    #         elif key == "ISSN":
    #             self.issn = value
    #             # TODO lookup ISSN using hub.toolforge.org like Houcemeddine?
    #             # if config.lookup_issn:
    #             #     qid = wikidata.lookup_issn(self.issn)
    #             #     if qid is not None:
    #             #         self.issn_qid = qid
    #         elif key == "published":
    #             if "date-parts" in value:
    #                 date_parts = value["date-parts"]
    #                 if len(date_parts) == 2:
    #                     # Assuming [%Y,%m]
    #                     self.issued = datetime(year=date_parts[0],
    #                                            month=date_parts[1])
    #             else:
    #                 pprint(value)
    #                 raise ValueError("this length of date parts is not supported yet")
    #                 # self.issued = datetime(value)
    #         elif key == "publisher-location":
    #             self.publisher_location = value
    #         elif key == "publisher":
    #             self.publisher = value
    #         elif key == "references-count":
    #             self.references_count = int(value)
    #         elif key == "URL":
    #             # This is the DOI url to the resolver.
    #             self.url = value
    #         elif key == "link":
    #             # This is fulltext links
    #             urls = None
    #             self.raw_links: Dict = self.data["link"]
    #             # Disabled for now
    #             # self.__parse_links__()
    #         elif key == "reference":
    #             self.references: List[Dict[str, str]] = value
    #         elif key == "license":
    #             # TODO detect garbage license URLs like
    #             # www.springer.com/tdm
    #             self.__license_url = value
    #             if self.__license_url is None:
    #                 logger.info("No license found for this article")
    #         elif key == "subject":
    #             self.raw_subjects = value
    #         else:
    #             logger.info(f"Skipping key: {key} with data: {value}")
