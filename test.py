import logging

from asseeibot.models.crossref_engine import CrossrefEngine
from asseeibot.models.identifiers.doi import Doi

logging.basicConfig(level=logging.WARNING)

doi = Doi(value="10.1038/d41586-020-03034-5")
c = CrossrefEngine(doi=doi)
#print(c.__dict__)