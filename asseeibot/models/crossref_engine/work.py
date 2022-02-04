#!/usr/bin/env python3
import logging
from typing import List, Any, Optional

from habanero import Crossref  # type: ignore
from pydantic import BaseModel, conint

from asseeibot.models.crossref_engine.author import CrossrefAuthor
from asseeibot.models.crossref_engine.date_parts import CrossrefDateParts
from asseeibot.models.crossref_engine.enums import CrossrefEntryType
from asseeibot.models.crossref_engine.link import CrossrefLink, CrossrefReference
from asseeibot.models.crossref_engine.ontology_based_ner_matcher import FuzzyMatch
from asseeibot.models.crossref_engine.subject import CrossrefSubject
from asseeibot.models.enums import MatchStatus
from asseeibot.models.identifier.isbn import Isbn

logger = logging.getLogger(__name__)


# class OrdinalWordToIntegerConverter(BaseModel):
#     word: str
#     words = ["first", "second"]
#
#     def get_integer(self):
#         if self.word in self.words:
#             for index, value in enumerate(self.words):
#                 if value == self.word:
#                     # Python lists are zero indexed so we +1 here
#                     return index + 1
#         else:
#             raise ValueError(f"{self.word} is not supported")


class CrossrefWork(BaseModel):
    __isbn: Optional[List[str]]
    __license_url: Optional[str]
    author: Optional[List[CrossrefAuthor]]
    doi: str
    is_referenced_by_count: Optional[conint(ge=0)]
    issn: Optional[List[str]]
    issn_qid: Optional[str]
    issued: Optional[CrossrefDateParts]
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
    source: str
    subject: Optional[List[str]]  # raw subjects
    subtitle: Optional[List[str]]
    title: Optional[List[Any]]

    raw_subjects: Optional[List[str]]
    already_matched_qids: List[str] = None
    subject_matches: List[FuzzyMatch] = None

    # url: str
    # xml_urls: Optional[List[str]]

    class Config:
        arbitrary_types_allowed = True

    @property
    def first_title(self):
        if self.title is not None and len(self.title) > 0:
            return self.title[0].replace('\n', '').strip()

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
    def number_of_subject_matches(self):
        number_of_matches = len(self.subject_matches)
        logger.debug(f"Nnumber of matches was {number_of_matches}")
        if number_of_matches > 0:
            return number_of_matches
        else:
            return 0

    @property
    def references(self):
        return self.reference
        # raise NotImplementedError("resolve the license url before returning")

    def __lookup_subjects__(self):
        """This models the science subject matcher

        It takes a list of subjects and returns supervised
        matches above a certain threshold if they are approved by the user.

        The threshold determines which matches to show to the user.
        The higher the closer the words are semantically calculated using
        https://en.wikipedia.org/wiki/Levenshtein_distance
        """
        logger.debug("__lookup_subjects__:Running")
        if self.raw_subjects is not None:
            self.already_matched_qids = []
            self.subject_matches = []
            for original_subject in self.raw_subjects:
                crossref_subject = CrossrefSubject(original_subject=original_subject)
                crossref_subject.lookup()
                if crossref_subject.match_status == MatchStatus.APPROVED:
                    logger.debug("Adding approved match to the list of matches")
                    if crossref_subject.matcher.match is None:
                        raise ValueError("crossref_subject.matcher.match was wrong")
                    self.subject_matches.append(crossref_subject.matcher.match)
                    self.already_matched_qids.append(crossref_subject.matcher.match.qid.value)
                elif crossref_subject.match_status == MatchStatus.DECLINED:
                    logger.debug("Ignoring declined match.")
                    # input("press enter")
                else:
                    logger.debug("No match")
                    # input("press enter")

    def __str__(self):
        return f"<{self.doi} [green][bold]{self.first_title}[/bold][/green] with {self.references_count} references>"

    def match_subjects_to_qids(self):
        logger.info(f"Matching subjects for {self.doi} now")
        if self.subject is not None:
            self.__lookup_subjects__()

    def pretty_print(self):
        from asseeibot.helpers.console import console
        console.print(f"<{self.doi} [bold orange]"
                      f"{self.first_title}[/bold orange] "
                      f"with {self.references_count} references and "
                      f"{f'the subjects ' + str(self.subject) if self.subject is not None else 'no subjects'}>")

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
    # def __parse_links__(self) -> None:
    #     """Parses the links into attributes"""
    #     logger = logging.getLogger(__name__)
    #     if self.raw_links is not None:
    #         # TODO make this async
    #         # Link is a field in the CrossrefEngine metadata
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
