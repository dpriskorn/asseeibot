import logging
from datetime import datetime, timezone
from time import sleep
from typing import Any
from urllib.parse import quote

import requests
from wikibaseintegrator import wbi_login, wbi_config, WikibaseIntegrator
from wikibaseintegrator.datatypes import Time, Item as WbiItemType, String
from wikibaseintegrator.entities.item import Item as WbiEntityItem
from wikibaseintegrator.wbi_enums import ActionIfExists

import asseeibot.runtime_variables
import config
from asseeibot.helpers.console import console
from asseeibot.helpers.wikidata import wikidata_query
from asseeibot.models.crossref.engine import CrossrefEngine
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.statistic_dataframe import StatisticDataframe
from asseeibot.models.wikimedia.enums import StatedIn, Property, DeterminationMethod
from asseeibot.models.wikimedia.wikidata.entity import EntityId
from asseeibot.models.wikimedia.wikidata.item import Item

logger = logging.getLogger(__name__)


class WikidataScientificItem(Item):
    doi: Any
    found_in_wikidata: bool = False
    qid: EntityId = None

    def __lookup_via_hub__(self) -> None:
        """Lookup via hub.toolforge.org
        It is way faster than WDQS
        https://hub.toolforge.org/doi:10.1111/j.1746-8361.1978.tb01321.x?site:wikidata?format=json"""
        logger.info("Looking up via Hub")
        url = f"https://hub.toolforge.org/doi:{self.doi.value}?site:wikidata?format=json"
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 302:
            logger.debug("Found QID via Hub")
            self.found_in_wikidata = True
            self.qid = EntityId(response.headers['Location'])
        elif response.status_code == 400:
            logger.debug("DOI not found via Hub")
            self.found_in_wikidata = False
        else:
            logger.error(f"Got {response.status_code} from Hub")
            console.print(response.json())
            exit()

    def lookup(self) -> None:
        self.__lookup_via_hub__()

    def __lookup_via_sparql__(self):
        logger.info(f"Looking up {self.doi.value} in Wikidata")
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
                logger.debug("Found in Wikidata!")
                self.found_in_wikidata = True
                self.qid = EntityId(raw_entity_id=df["item"][0])
                # exit()
            elif len(df) > 1:
                print(repr(df))
                logger.error(f"Got more than one match on {self.doi.value} in WD. "
                             f"Please check if they are duplicates and should be merged. "
                             f"{self.wikidata_doi_search_url()}"
                             f"Sleeping for 10s.")
                sleep(10)
                self.found_in_wikidata = True
            else:
                logger.debug("Not found in Wikidata")
                self.found_in_wikidata = False

    def __add_main_subject__(
            self,
            match: FuzzyMatch
    ) -> None:
        """This adds a main subject to the item

        It only has side effects"""
        logger = logging.getLogger(__name__)
        if match.qid is None or match.qid == "":
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
        stated_in = WbiItemType(
            prop_nr="P248",
            value=StatedIn.CROSSREF.value
        )
        stated_as = String(
            prop_nr=Property.STATED_AS.value,
            value=match.original_subject
        )
        determination_method = WbiItemType(
            prop_nr=Property.DETERMINATION_METHOD.value,
            value=DeterminationMethod.FUZZY_POWERED_NAMED_ENTITY_RECOGNITION_MATCHER.value
        )
        reference = [
            stated_in,
            stated_as,
            retrieved_date,
            determination_method,
        ]
        if reference is None:
            raise ValueError("No reference defined, cannot add usage example")
        else:
            # This is the usage example statement
            claim = WbiItemType(
                prop_nr=Property.MAIN_SUBJECT.value,
                value=match.qid.value,
                # Add qualifiers
                qualifiers=[],
                # Add reference
                references=[reference],
            )
            # if config.debug_json:
            #     logging.debug(f"claim:{claim.get_json_representation()}")
            if asseeibot.runtime_variables.login_instance is None:
                # Authenticate with WikibaseIntegrator
                with console.status("Logging in with WikibaseIntegrator..."):
                    asseeibot.runtime_variables.login_instance = wbi_login.Login(
                        user=config.bot_username,
                        password=config.password
                    )
                    # Set User-Agent
                    wbi_config.config["USER_AGENT_DEFAULT"] = config.user_agent
            wbi = WikibaseIntegrator(login=asseeibot.runtime_variables.login_instance)
            item = wbi.item.get(self.qid.value)
            item.add_claims(
                [claim],
                # This means that if the value already exist we will update it.
                action_if_exists=ActionIfExists.APPEND
            )
            # if config.debug_json:
            #     print(item.get_json_representation())
            # TODO match.label could be None, do we need to handle that?
            result = item.write(
                summary=(f"Added main subject [[{match.qid}|{match.label}]] " +
                         f"with [[Wikidata:Tools/asseeibot]] v{config.version}")
            )
            if isinstance(result, WbiEntityItem):
                console.print(f"[green]Uploaded '{match.label}' to[/green] {self.qid.url()}")
                match.edited_qid = self.qid
                upload_dataframe = StatisticDataframe()
                upload_dataframe.update_forward_refs()
                upload_dataframe.match = match
                upload_dataframe.add()
            else:
                raise ValueError("Did not get an item back from WBI, something went wrong :/")
            # print("debug exit after adding to statistics")
            # exit()

    def add_subjects(self, crossref: CrossrefEngine):
        logger = logging.getLogger(__name__)
        if crossref.work is not None:
            # print_match_table(crossref)
            logger.info(f"Adding {crossref.work.number_of_subject_matches} now to {self.qid.url()}")
            for match in crossref.work.ner.subject_matches:
                self.__add_main_subject__(match=match)

    def wikidata_doi_search_url(self):
        # quote to guard against äöå and the like
        return (
                "https://www.wikidata.org/w/index.php?" +
                "search={}&title=Special%3ASearch&".format(quote(self.doi.value)) +
                "profile=advanced&fulltext=0&" +
                "advancedSearch-current=%7B%7D&ns0=1"
        )
