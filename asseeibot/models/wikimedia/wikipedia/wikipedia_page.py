from __future__ import annotations

import json
import logging
from typing import List, Any, TYPE_CHECKING, Optional

import pywikibot  # type: ignore
from pydantic import BaseModel
from pywikibot import Page

import config
from asseeibot.helpers.console import console
from asseeibot.models.wikimedia.wikipedia.templates.enwp.cite_journal import CiteJournal
from asseeibot.models.wikimedia.wikipedia.templates.wikipedia_page_reference import WikipediaPageReference

if TYPE_CHECKING:
    from asseeibot.models.identifier.doi import Doi

logger = logging.getLogger(__name__)


# This is a hack. Copying it here avoids an otherwise seemingly unavoidable cascade of pydantic errors...


class WikipediaPage(BaseModel):
    """Models a WMF Wikipedia page"""
    pywikibot_page: Optional[Page] = None
    dois: Optional[List[Doi]] = None
    missing_dois: Optional[List[Doi]] = None
    number_of_dois: int = 0
    number_of_isbns: int = 0
    number_of_missing_dois: int = 0
    number_of_missing_isbns: int = 0
    page_id: Optional[int] = None
    references: Optional[List[WikipediaPageReference]] = None
    title: Optional[str] = None
    # We can't type this with WikimediaEvent because of pydantic
    wikimedia_event: Any

    class Config:
        arbitrary_types_allowed = True

    def __calculate_statistics__(self):
        self.number_of_dois = len(self.dois)
        self.number_of_missing_dois = len(self.missing_dois)
        logger.info(f"{self.number_of_missing_dois} out of {self.number_of_dois} "
                    f"DOIs on this page were missing in Wikidata")
        # if len(missing_dois) > 0:
        #     input_output.save_to_wikipedia_list(missing_dois, language_code, title)
        # if config.import_mode:
        # answer = util.yes_no_question(
        #     f"{doi} is missing in WD. Do you"+
        #     " want to add it now?"
        # )
        # if answer:
        #     crossref_engine.lookup_data(doi=doi, in_wikipedia=True)
        #     pass
        # else:
        #     pass

    def start(self):
        if self.wikimedia_event is None:
            raise ValueError("wikimedia_event was None")
        self.__get_title_from_event__()
        self.__get_wikipedia_page__()
        self.__parse_templates__()
        self.__lookup_and_match_and_populate_missing_dois__()
        self.__upload_all_subjects_matched_to_wikidata__()
        self.__calculate_statistics__()

    def __get_title_from_event__(self):
        self.title = self.wikimedia_event.page_title
        if self.title is None or self.title == "":
            raise ValueError("title not set correctly")

    def __get_wikipedia_page__(self):
        """Get the page from Wikipedia"""
        logger.info("Fetching the wikitext")
        self.pywikibot_page = pywikibot.Page(self.wikimedia_event.event_stream.pywikibot_site, self.title)
        # this id is useful when talking to WikipediaCitations because it is unique
        self.page_id = int(self.pywikibot_page.pageid)

    # def __match_subjects__(self):
    #     logger.info(f"Matching subjects from {len(self.dois) - self.number_of_missing_dois} DOIs")
    #     [doi.wikidata_scientific_item.crossref_engine.work.match_subjects_to_qids() for doi in self.dois
    #      if (
    #              doi.wikidata_scientific_item.doi_found_in_wikidata and
    #              doi.wikidata_scientific_item.crossref_engine is not None and
    #              doi.wikidata_scientific_item.crossref_engine.work is not None
    #      )]

    def __parse_templates__(self):
        """We parse all the templates into WikipediaPageReferences"""
        logger.info("Parsing templates")
        raw = self.pywikibot_page.raw_extracted_templates
        self.references = []
        self.dois = []
        for template_name, content in raw:
            # logger.debug(f"working on {template_name}")
            if template_name.lower() == "cite journal":
                # Workaround from https://stackoverflow.com/questions/56494304/how-can-i-do-to-convert-ordereddict-to
                # -dict First we convert the list of tuples to a normal dict
                content_as_dict = json.loads(json.dumps(content))
                # Then we add the dict to the "doi" key that pydantic expects
                # logger.debug(f"content_dict:{content_as_dict}")
                # if "doi" in content_as_dict:
                #     doi = content_as_dict["doi"]
                #     content_as_dict["doi"] = dict(
                #         value=doi
                #     )
                # else:
                #     content_as_dict["doi"] = None
                cite_journal = CiteJournal(**content_as_dict)
                self.references.append(cite_journal)
                if cite_journal.doi is not None:
                    from asseeibot.models.identifier.doi import Doi
                    doi = Doi(value=cite_journal.doi)
                    doi.__test_doi__()
                    if doi.regex_validated:
                        self.number_of_dois += 1
                        self.dois.append(doi)
                else:
                    # We ignore cultural magazines for now
                    if cite_journal.journal_title is not None and "magazine" not in cite_journal.journal_title:
                        logger.warning(f"An article titled {cite_journal.title} "
                                       f"in the journal_title {cite_journal.journal_title} "
                                       f"was found but no DOI. "
                                       f"(pmid:{cite_journal.pmid} jstor:{cite_journal.jstor})")
        # exit()

    def __lookup_and_match_and_populate_missing_dois__(self):
        logger.debug("__lookup_and_match_and_populate_missing_dois__:Populating missing DOIs")
        # exit()
        self.missing_dois = []
        if self.dois is not None and len(self.dois) > 0:
            logger.info(f"Looking up {self.number_of_dois} DOIs in "
                        f"Crossref and Wikidata")
            [doi.test_doi_then_lookup_in_crossref_and_then_in_wikidata_and_then_match_subjects() for doi in self.dois]
            missing_dois = [doi for doi in self.dois if not doi.wikidata_scientific_item.doi_found_in_wikidata]
            if missing_dois is not None and len(missing_dois) > 0:
                self.missing_dois.extend(missing_dois)
        self.number_of_missing_dois = len(self.missing_dois)
        if self.number_of_missing_dois > 0:
            logger.info(f"Found {self.number_of_missing_dois} missing DOIs on the page '{self.title}")
            if config.loglevel == logging.DEBUG:
                logger.debug("Done populating DOIs")
                console.print(self.missing_dois)
                # input("press enter after printing dois")

    def __upload_all_subjects_matched_to_wikidata__(self):
        if config.match_subjects_to_qids_and_upload:
            logger.debug("__upload_all_subjects_matched_to_wikidata__:Calculating the number of matches to upload")
            number_of_subject_matches = sum(
                [doi.wikidata_scientific_item.crossref.work.number_of_subject_matches for doi in self.dois
                 if (
                    doi.wikidata_scientific_item.crossref is not None and
                    doi.wikidata_scientific_item.crossref.work is not None and
                    doi.wikidata_scientific_item.crossref.work.number_of_subject_matches is not None
                 )]
            )
            if number_of_subject_matches > 0:
                from asseeibot.helpers.tables import print_all_matches_table
                print_all_matches_table(self)
                if config.press_enter_confirmations:
                    input("press enter to continue upload or ctrl+c to quit")
                [doi.wikidata_scientific_item.upload_subjects() for doi in self.dois]
            else:
                if len(self.dois) == 0:
                    logger.debug("__upload_all_subjects_matched_to_wikidata__:No DOIs found in this page")
                else:
                    if config.loglevel == logging.DEBUG:
                        # logger.debug(f"__upload_all_subjects_matched_to_wikidata__:
                        # Found no matches to upload for the following DOIs found in {self.title}")
                        input("press enter to continue after no matches found")
                    # console.print(self.dois)
                    # exit()
