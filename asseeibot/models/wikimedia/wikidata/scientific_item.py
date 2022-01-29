import logging
from datetime import datetime
from time import sleep, timezone
from typing import Any, List, Set
from urllib.parse import quote

from wikibaseintegrator import wbi_login, wbi_config, WikibaseIntegrator
from wikibaseintegrator.datatypes import Time
from wikibaseintegrator.entities import Item as WbiItem
from wikibaseintegrator.wbi_enums import ActionIfExists

import config
from asseeibot.helpers.console import console
from asseeibot.helpers.wikidata import wikidata_query
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.wikimedia.enums import StatedIn, Property, DeterminationMethod
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

    def __add_main_subject__(
            self,
            qid: str
    ) -> None:
        """This adds a main subject to the item

        It only has side effects"""
        logger = logging.getLogger(__name__)
        if qid is None or qid == "":
            raise ValueError("qid was None or empty string")
        logger.info("Adding main subject with WBI")
        # Use WikibaseIntegrator aka wbi to upload the changes in one edit
        retrieved_date = Time(
            prop_nr="P813",  # Fetched today
            time=datetime.utcnow().replace(
                tzinfo=timezone.utc
            ).replace(
                hour=0,
                minute=0,
                second=0,
            ).strftime("+%Y-%m-%dT%H:%M:%SZ")
        )
        stated_in = WbiItem(
            prop_nr="P248",
            value=StatedIn.CROSSREF.value
        )
        determination_method = WbiItem(
            prop_nr=Property.DETERMINATION_METHOD.value,
            value=DeterminationMethod.FUZZY_POWERED_NAMED_ENTITY_RECOGNITION_MATCHER.value
        )
        reference = [
            stated_in,
            retrieved_date,
            determination_method,
        ]
        if reference is None:
            raise ValueError("No reference defined, cannot add usage example")
        else:
            # This is the usage example statement
            claim = WbiItem(
                prop_nr=Property.MAIN_SUBJECT.value,
                value=qid,
                # Add qualifiers
                qualifiers=[],
                # Add reference
                references=[reference],
            )
            # if config.debug_json:
            #     logging.debug(f"claim:{claim.get_json_representation()}")
            if config.login_instance is None:
                # Authenticate with WikibaseIntegrator
                with console.status("Logging in with WikibaseIntegrator..."):
                    config.login_instance = wbi_login.Login(
                        auth_method='login',
                        user=config.username,
                        password=config.password,
                        debug=False
                    )
                    # Set User-Agent
                    wbi_config.config["USER_AGENT_DEFAULT"] = config.user_agent
            wbi = WikibaseIntegrator(login=config.login_instance)
            item = wbi.item.get(self.qid.value)
            item.add_claims(
                [claim],
                # This means that if the value already exist we will update it.
                action_if_exists=ActionIfExists.REPLACE
            )
            # if config.debug_json:
            #     print(item.get_json_representation())
            result = item.write(
                summary=(f"Added main subject {{{{Q|{qid}}}}} " +
                         f"with [[Wikidata:Tools/asseeibot]] v{config.version}")
            )
            # logging.debug(f"result from WBI:{result}")
            # TODO add handling of result from WBI and return True == Success or False
            print("debug exit")
            exit()
            return result

    def add_subjects(self, subject_qids: Set[str]):
        for qid in subject_qids:
            self.__add_main_subject__(qid=qid)

    def wikidata_doi_search_url(self):
        # quote to guard against äöå and the like
        return (
                "https://www.wikidata.org/w/index.php?" +
                "search={}&title=Special%3ASearch&".format(quote(self.doi.value)) +
                "profile=advanced&fulltext=0&" +
                "advancedSearch-current=%7B%7D&ns0=1"
        )
