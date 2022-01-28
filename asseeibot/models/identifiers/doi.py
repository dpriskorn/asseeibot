import logging
import re

from asseeibot.helpers.console import console
from asseeibot.models.crossref_engine import CrossrefEngine
from asseeibot.models.crossref_work import CrossrefWork
from asseeibot.models.identifier import Identifier
from asseeibot.models.wikimedia.wikidata_scientific_item import WikidataScientificItem


# @dataclass
class Doi(Identifier):
    """Models a DOI"""
    crossref_entry: CrossrefWork = None
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
        self.crossref_entry = crossref.lookup_work()
        if self.crossref_entry is not None:
            self.found_in_crossref = True

    def lookup_in_wikidata(self):
        self.wikidata_scientific_item = WikidataScientificItem(doi=self)
        self.found_in_wikidata = self.wikidata_scientific_item.found_in_wikidata

    def upload_subjects_to_wikidata(self):
        if (
                self.found_in_wikidata and
                self.found_in_crossref and
                len(self.crossref_entry.subject_qids) > 0
        ):
            # pseudo
            for qid in self.crossref_entry.subject_qids:
                # prepare WBI claim
                pass
            # do upload to WD
            # we care if they are already present,
            # so we setup WBI to abort if found
            console.print("Upload done")
        else:
            console.print("No subject Q-items matched for this DOI")
