import logging
import re

from asseeibot.models.crossref_work import CrossrefWork
from asseeibot.models.identifier import Identifier
from asseeibot.models.wikimedia.wikidata_scientific_item import WikidataScientificItem


#@dataclass
class Doi(Identifier):
    """Models a DOI"""
    crossref_entry: CrossrefWork = None
    wikidata_scientific_item: WikidataScientificItem = None
    regex_validated: bool = True

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
        self.crossref_entry = CrossrefWork(doi=self)

    def lookup_in_wikidata(self):
        self.wikidata_scientific_item = WikidataScientificItem(doi=self)
        self.found_in_wikidata = self.wikidata_scientific_item.found_in_wikidata

