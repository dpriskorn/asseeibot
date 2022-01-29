import logging
import re

from asseeibot.models.crossref.engine import CrossrefEngine
from asseeibot.models.crossref.work import CrossrefWork
from asseeibot.models.identifiers.identifier import Identifier


# @dataclass
from asseeibot.models.wikimedia.wikidata.scientific_item import WikidataScientificItem


class Doi(Identifier):
    """Models a DOI"""
    crossref_work: CrossrefWork = None
    wikidata_scientific_item: WikidataScientificItem = None
    regex_validated: bool = True
    found_in_crossref: bool = False
    found_in_wikidata: bool = False

    def __post_init_post_parse__(self):
        logger = logging.getLogger(__name__)
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
        logger = logging.getLogger(__name__)
        logger.debug(f"Looking up {self.value} in Crossref")
        crossref = CrossrefEngine(doi=self)
        self.crossref_work = crossref.lookup_work()
        if self.crossref_work is not None:
            self.found_in_crossref = True

    def lookup_in_wikidata(self):
        self.wikidata_scientific_item = WikidataScientificItem(doi=self)
        self.wikidata_scientific_item.lookup()
        self.found_in_wikidata = self.wikidata_scientific_item.found_in_wikidata

    def upload_subjects_to_wikidata(self):
        logger = logging.getLogger(__name__)
        if (
                self.found_in_wikidata and
                self.found_in_crossref
        ):
            logger.debug("Found in both WD and Crossref")
            if (
                    self.crossref_work.number_of_subject_matches > 0
            ):
                logger.info("Uploading now")
                self.wikidata_scientific_item.add_subjects(self.crossref_work)
            else:
                logger.debug("No subject Q-items matched for this DOI")
        else:
            logger.debug("Not found in both WD and Crossref")
