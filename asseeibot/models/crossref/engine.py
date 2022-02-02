import logging
from time import sleep
from typing import Any, Dict

import requests
from caseconverter import snakecase
from habanero import Crossref
from pydantic import BaseModel
from requests import HTTPError, JSONDecodeError

import config
from asseeibot.helpers.console import console
from asseeibot.helpers.tables import print_match_table
from asseeibot.models.crossref.enums import CrossrefEntryType
from asseeibot.models.crossref.work import CrossrefWork


class CrossrefEngine(BaseModel):
    """Lookup a work in Crossref"""
    doi: Any = None  # We can't type this to Doi because of a forwardref error
    result: Any = None
    work: CrossrefWork = None
    data: Any = None
    object_type: str = None

    def __convert_to_snake_case__(self):
        """This converts to snakecase 2 levels down in the dictionary

        It is needed because pydantic cannot map e.g. "short-title" -> "short_title"

        See also https://github.com/nficano/humps which does not support kebabcase yet"""

        def dekebabcase_dictionary_keys(dictionary) -> Dict:
            if dictionary is None:
                raise ValueError("dictionary was None")
            new_dictionary = dict()
            for key in dictionary.keys():
                value = dictionary[key]
                renamed_key = snakecase(key).lower()
                new_dictionary[renamed_key] = value
            return new_dictionary

        logger = logging.getLogger(__name__)
        # pseudo code
        # we have a dict with keys
        data = self.data
        finished_data = dict()
        for key in data.keys():
            value = data[key]
            if isinstance(value, dict):
                # data[key]
                new_value = dekebabcase_dictionary_keys(value)
                value = new_value
            if isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        item = dekebabcase_dictionary_keys(item)
                    new_list.append(item)
                value = new_list
            renamed_key = snakecase(key).lower()
            finished_data[renamed_key] = value
        # if config.loglevel == logging.DEBUG:
        #     logger.debug("Here is the renamed dict")
        #     console.print(finished_data)
        self.data = finished_data

    def __lookup_work__(self):
        """Lookup the data"""
        logger = logging.getLogger(__name__)
        # https://www.crossref.org/education/retrieve-metadata/rest-api/
        # async client here https://github.com/izihawa/aiocrossref but only 1 contributor
        # https://github.com/sckott/habanero >6 contributors not async
        logger.debug(f"Looking up work {self.doi.value} in Crossref")
        # logging.info("Looking up from Crossref")
        cr = Crossref(mailto=config.crossref_polite_pool_email)
        # result = cr.works(doi=doi)
        try:
            self.result = cr.works(ids=self.doi.value)
        except (HTTPError, ConnectionError, JSONDecodeError) as e:
            logger.error(f"Got error from Crossref: {e}")

    def __parse_habanero_data__(self):
        logger = logging.getLogger(__name__)
        if self.result is not None:
            # print(result.keys())
            if "message" in self.result:
                self.data = self.result["message"]
                # pprint(self.data)
                # exit(0)
                if "type" in self.data:
                    self.object_type = CrossrefEntryType(self.data["type"])
                    if self.object_type == "book":
                        logger.info("Book detected, we exclude those for now.")
                        return None
                    else:
                        logger.debug(f"Parsing the following crossref data now")
                        # if config.loglevel == logging.DEBUG:
                        #     logger.debug("Data from Habanero")
                        #     console.print(self.data)
                        self.__convert_to_snake_case__()
                        work = CrossrefWork(**self.data)
                        if work is not None:
                            # if config.loglevel == logging.DEBUG:
                            #     logger.debug("Finished model dict")
                            #     console.print(work.dict())
                            console.print(work)
                        self.work = work
                        # exit(0)
                else:
                    raise ValueError("type not found")
            else:
                logger.error("no message dict in result from Crossref")
                sleep(10)

    def __print_matches_found__(self):
        if self.work.number_of_subject_matches > 0:
            print_match_table(self.work)

    def lookup_work(self):
        """Lookup, parse and match subjects and store the
        CrossrefWork in the attribute self.work"""
        self.__lookup_work__()
        self.__parse_habanero_data__()

    def match_subjects(self):
        """Match subjects"""
        if config.match_subjects_to_qids_and_upload and self.work is not None:
            self.work.match_subjects_to_qids()
            # Disabled because we print all matches in the end instead for better UX
            # self.__print_matches_found__()
