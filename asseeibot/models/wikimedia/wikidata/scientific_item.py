import logging
from time import sleep
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel

import config
from asseeibot.helpers.wikidata import wikidata_query
from asseeibot.models.wikimedia.wikidata.entity import EntityId
from asseeibot.models.wikimedia.wikidata.item import Item


class WikidataScientificItem(Item):
    doi: Any
    found_in_wikidata: bool = False
    qid: EntityId = None

    def __post_init_post_parse__(self):
        self.__lookup__()

    def __lookup__(self):
        logger = logging.getLogger(__name__)
        logger.info(f"looking up: {self.doi.value}")
        # TODO use the cirrussearch API instead?
        df = wikidata_query(f'''
            SELECT DISTINCT ?item
            WHERE 
            {{
            {{
            ?item wdt:P356 "{self.doi.value}".
            }} union {{
            ?item wdt:P356 "{self.doi.value.lower()}".
            }} union {{
            ?item wdt:P356 "{self.doi.value.upper()}".
            }} 
            }}
            ''')
        # print(df)
        if df is not None:
            # print(df.info())
            # print(f"df length: {len(df)}")
            # exit()
            if len(df) == 1:
                self.found_in_wikidata = True
                self.qid = EntityId(raw_entity_id=df["item"][0])
                # exit()
            elif len(df) > 1:
                print(repr(df))
                logger.error(f"Got more than one match on {self.doi.value} in WD. "
                             f"Please check if they are duplicates and should be merged. {self.wikidata_doi_search_url()}"
                             f"Sleeping for 10s.")
                sleep(10)
                self.found_in_wikidata = True
            else:
                self.found_in_wikidata = False

    def add_subjects(self, subject_qids):
        raise NotImplementedError
        # for qid in subject_qids:
        #     # prepare WBI claim
        #     pass
        # do upload to WD
        # we care if they are already present,
        # so we setup WBI to abort if found
        # console.print("Upload done")

    def wikidata_doi_search_url(self):
        # quote to guard against äöå and the like
        return (
                "https://www.wikidata.org/w/index.php?" +
                "search={}&title=Special%3ASearch&".format(quote(self.doi.value)) +
                "profile=advanced&fulltext=0&" +
                "advancedSearch-current=%7B%7D&ns0=1"
        )
