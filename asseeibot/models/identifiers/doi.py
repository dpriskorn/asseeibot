import logging
import re

from asseeibot.models.crossref.engine import CrossrefEngine
from asseeibot.models.identifiers.identifier import Identifier
# @dataclass
from asseeibot.models.wikimedia.wikidata.scientific_item import WikidataScientificItem

logger = logging.getLogger(__name__)


class Doi(Identifier):
    """Models a DOI"""
    crossref: CrossrefEngine = None
    wikidata_scientific_item: WikidataScientificItem = None
    regex_validated: bool = True
    found_in_crossref: bool = False
    found_in_wikidata: bool = False

    def __post_init_post_parse__(self):
        # todo test it with a regex on init
        doi_regex_pattern = "^10.\d{4,9}\/+.+$"
        if re.match(doi_regex_pattern, self.value) is None:
            self.regex_validated = False
            logger.error(f"{self.value} did not match the doi regex")

    def __str__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.value.upper()

    def __repr__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.value.upper()

    def lookup_in_crossref(self):
        """Lookup in Crossref and parse the whole result into an object we can use"""
        logger.debug(f"Looking up {self.value} in Crossref")
        self.crossref = CrossrefEngine(doi=self)
        self.crossref.lookup_work()
        if self.crossref.work is not None:
            # This helps us easily in WikipediaPage to get an overview
            self.found_in_crossref = True
        else:
            self.found_in_crossref = False

    def __lookup_in_crossref_and_then_wikidata__(self):
        self.wikidata_scientific_item = WikidataScientificItem(doi=self)
        self.wikidata_scientific_item.lookup()
        self.found_in_wikidata = self.wikidata_scientific_item.found_in_wikidata

    def lookup_and_match_subjects(self):
        """Looking up in Wikidata also entails looking"""
        self.__lookup_in_crossref_and_then_wikidata__()
        if self.crossref is not None:
            self.crossref.match_subjects()

    def upload_subjects_to_wikidata(self):
        """Upload all the matched subjects to Wikidata"""
        if (
                self.found_in_wikidata and
                self.found_in_crossref
        ):
            logger.debug("Found in both WD and Crossref")
            if (
                    self.crossref.work.number_of_subject_matches > 0
            ):
                logger.info("Uploading now")
                self.wikidata_scientific_item.add_subjects(self.crossref)
            else:
                logger.debug("No subject Q-items matched for this DOI")
        else:
            logger.debug("Not found in both WD and Crossref")
