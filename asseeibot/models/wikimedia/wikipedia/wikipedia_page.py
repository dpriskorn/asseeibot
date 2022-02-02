from __future__ import annotations

import json
import logging
import re
from typing import List, Any, TYPE_CHECKING

import pywikibot
from pywikibot import Page

import config
from asseeibot.helpers.console import console
from asseeibot.models.identifiers.identifier import Identifier
from asseeibot.models.wikimedia.wikidata.scientific_item import WikidataScientificItem
from asseeibot.models.wikimedia.wikipedia.templates.enwp.cite_journal import CiteJournal
from asseeibot.models.wikimedia.wikipedia.wikipedia_page_reference import WikipediaPageReference

if TYPE_CHECKING:
    from asseeibot.models.crossref.engine import CrossrefEngine

logger = logging.getLogger(__name__)


# This is a hack. Copying it here avoids an otherwise seemingly unavoidable cascade of pydantic errors...
# BaseModel
class Doi(Identifier):
    """Models a DOI"""
    crossref: CrossrefEngine = None
    wikidata_scientific_item: WikidataScientificItem = None
    regex_validated: bool = True
    found_in_crossref: bool = False
    found_in_wikidata: bool = False

    def __repr__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.value.upper()

    def __str__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.value.upper()

    def __test_doi__(self):
        doi_regex_pattern = "^10.\d{4,9}\/+.+$"
        if re.match(doi_regex_pattern, self.value) is None:
            self.regex_validated = False
            logger.error(f"{self.value} did not match the doi regex")
            exit()

    def lookup_in_crossref(self):
        """Lookup in Crossref and parse the whole result into an object we can use"""
        from asseeibot.models.crossref.engine import CrossrefEngine
        logger.debug(f"Looking up {self.value} in Crossref")
        self.crossref = CrossrefEngine()
        # self.crossref.update_forward_refs()
        self.crossref.doi = self
        self.crossref.lookup_work()
        if self.crossref.work is not None:
            # This helps us easily in WikipediaPage to get an overview
            self.found_in_crossref = True
        else:
            self.found_in_crossref = False

    def __lookup_in_crossref_and_then_wikidata__(self):
        self.wikidata_scientific_item = WikidataScientificItem(doi=self)
        self.wikidata_scientific_item.lookup_in_crossref_and_then_wikidata()
        self.found_in_wikidata = self.wikidata_scientific_item.found_in_wikidata

    def lookup_and_match_subjects(self):
        """Looking up in Crossref, Wikidata and match subjects only if found in both"""
        self.__lookup_in_crossref_and_then_wikidata__()
        if self.crossref is not None and self.crossref.work is not None:
            logger.debug("Found in crossref")
            if self.found_in_wikidata:
                logger.info(f"Matching subjects for {self.value} now")
                self.crossref.match_subjects()
                # print("debug exit after matching subjects")
                # exit()
            else:
                logger.debug("Not found in Wikidata, skipping lookup of subjects")
        else:
            logger.debug("Not found in crossref")

    def upload_subjects_to_wikidata(self):
        """Upload all the matched subjects to Wikidata"""
        if (
                self.found_in_wikidata and
                self.found_in_crossref
        ):
            if (
                    self.crossref.work.number_of_subject_matches > 0
            ):
                logger.info(f"Uploading matched subjects for {self.value} now")
                self.wikidata_scientific_item.add_subjects(self.crossref)
            else:
                logger.debug("No subject Q-items matched for this DOI")
        else:
            logger.warning("DOI not found in both Wikidata and Crossref")


class WikipediaPage:
    """Models a WMF Wikipedia page"""
    number_of_dois: int = 0
    number_of_isbns: int = 0
    number_of_missing_dois: int = 0
    number_of_missing_isbns: int = 0
    page_id: int = None
    pywikibot_page: Page = None
    references: List[WikipediaPageReference] = None
    title: str = None
    # We can't type this with WikimediaEvent because of pydantic
    wikimedia_event: Any = None
    # We can't type these with Doi because of pydantic
    missing_dois: List[Doi] = None
    dois: List[Doi] = None

    def __init__(
            self,
            wikimedia_event: Any = None
    ):
        """Get the page from Wikipedia"""
        if wikimedia_event is None:
            raise ValueError("wikimedia_event was None")
        self.wikimedia_event = wikimedia_event
        self.title = self.wikimedia_event.page_title
        if self.title is None or self.title == "":
            raise ValueError("title not set correctly")
        logger.info("Fetching the wikitext")
        self.pywikibot_page = pywikibot.Page(self.wikimedia_event.event_stream.pywikibot_site, self.title)
        self.page_id = int(self.pywikibot_page.pageid)
        self.__parse_templates__()
        self.__populate_missing_dois__()
        self.__upload_all_subjects_matched_to_wikidata__()
        self.__calculate_statistics__()

    def __parse_templates__(self):
        """We parse all the templates into WikipediaPageReferences"""
        logger = logging.getLogger(__name__)
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

    def __populate_missing_dois__(self):
        logger.debug("Populating missing DOIs")
        # exit()
        self.missing_dois = []
        if self.dois is not None and len(self.dois) > 0:
            logger.info(f"Looking up {self.number_of_dois} DOIs in "
                        f"Wikidata and if found also in Crossref")
            for doi in self.dois:
                if not isinstance(doi, Doi):
                    raise ValueError("not instance of DOI")
            [doi.lookup_and_match_subjects() for doi in self.dois]
            missing_dois = [doi for doi in self.dois if not doi.found_in_wikidata]
            if missing_dois is not None and len(missing_dois) > 0:
                self.missing_dois.extend(missing_dois)
        if len(self.missing_dois) > 0:
            if config.loglevel == logging.DEBUG:
                logger.debug("Done populating DOIs")
                console.print(self.missing_dois)
                # exit()

    def __upload_all_subjects_matched_to_wikidata__(self):
        if config.match_subjects_to_qids_and_upload:
            logger.debug("Calculating the number of matches to upload")
            number_of_subject_matches = sum(
                [doi.crossref.work.number_of_subject_matches for doi in self.dois
                 if doi.crossref is not None and doi.crossref.work is not None]
            )
            if number_of_subject_matches > 0:
                console.print(f"Uploading {number_of_subject_matches} subjects to Wikidata "
                              f"found via DOIs on the Wikipedia page {self.title}")
                from asseeibot.helpers.tables import print_all_matches_table
                print_all_matches_table(self)
                if config.press_enter_confirmations:
                    input("press enter to continue upload or ctrl+c to quit")
                [doi.upload_subjects_to_wikidata() for doi in self.dois]
            else:
                if len(self.dois) == 0:
                    logger.debug("No DOIs found in this page")
                else:
                    logger.debug(f"Found no matches to upload for the following DOIs found in {self.title}")
                    console.print(self.dois)
                    # exit()

    def __calculate_statistics__(self):
        self.number_of_dois = len(self.dois)
        self.number_of_missing_dois = len(self.missing_dois)
        logger.info(f"Found {self.number_of_missing_dois}/{self.number_of_dois} missing DOIs on this page")
        # if len(missing_dois) > 0:
        #     input_output.save_to_wikipedia_list(missing_dois, language_code, title)
        # if config.import_mode:
        # answer = util.yes_no_question(
        #     f"{doi} is missing in WD. Do you"+
        #     " want to add it now?"
        # )
        # if answer:
        #     crossref.lookup_data(doi=doi, in_wikipedia=True)
        #     pass
        # else:
        #     pass
