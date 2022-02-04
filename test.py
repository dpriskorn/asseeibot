import logging

from asseeibot.models.crossref_engine.__init__ import CrossrefEngine

logging.basicConfig(level=logging.DEBUG)

# doi = Doi(value="10.1038/d41586-020-03034-5")
doi = "10.1109/ICKEA.2016.7803013"
c = CrossrefEngine(wikipedia_doi=doi)
# print(c.__dict__)
