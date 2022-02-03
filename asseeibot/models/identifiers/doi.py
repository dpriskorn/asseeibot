import logging
import re

from asseeibot.models.identifiers.identifier import Identifier
# @dataclass
from asseeibot.models.wikimedia.wikidata.scientific_item import WikidataScientificItem

logger = logging.getLogger(__name__)


# BaseModel
class Doi(Identifier):
    """Models a DOI"""
    regex_validated: bool = True
    wikidata_scientific_item: WikidataScientificItem = None

    def lookup_in_crossref_and_then_in_wikidata(self):
        self.__test_doi__()
        if self.regex_validated:
            self.wikidata_scientific_item = WikidataScientificItem(
                wikipedia_doi=self.value,
            )
            self.wikidata_scientific_item.lookup_and_match_subjects()

    def __repr__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.value.upper()

    def __test_doi__(self):
        doi_regex_pattern = "^10.\d{4,9}\/+.+$"
        if self.value == "":
            logger.error("DOI was empty string")
        else:
            if re.match(doi_regex_pattern, self.value) is None:
                self.regex_validated = False
                logger.error(f"{self.value} did not match the doi regex")

