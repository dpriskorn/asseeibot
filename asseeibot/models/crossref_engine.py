import logging
from copy import deepcopy
from typing import Optional, Any, Dict

from caseconverter import snakecase
from habanero import Crossref
from pydantic.dataclasses import dataclass
from requests import HTTPError

from asseeibot import config
from asseeibot.helpers.console import console
from asseeibot.models.crossref_enums import CrossrefEntryType
from asseeibot.models.crossref_work import CrossrefWork


@dataclass
class CrossrefEngine:
    """Lookup a work in Crossref"""
    doi: Any
    result: Any = None

    def __post_init_post_parse__(self):
        logger = logging.getLogger(__name__)
        logger.debug(f"Looking up work {self.doi.value} in Crossref")
        work = self.lookup_work()

    def lookup_work(self) -> Optional[CrossrefWork]:
        """Lookup data and populate the object"""
        logger = logging.getLogger(__name__)
        # https://www.crossref.org/education/retrieve-metadata/rest-api/
        # async client here https://github.com/izihawa/aiocrossref but only 1 contributor
        # https://github.com/sckott/habanero >6 contributors not async
        logging.info("Looking up from Crossref")
        cr = Crossref()
        # result = cr.works(doi=doi)
        try:
            self.result = cr.works(ids=self.doi.value)
        except (HTTPError, ConnectionError) as e:
            logger.error(f"Got error from Crossref: {e}")
        work = self.__parse_habanero_data__()
        if config.match_subjects_to_qids_and_upload and work is not None:
            work.match_subjects_to_qids()
            if len(work.subject_qids) > 0:
                console.print(f"The following main subjects can "
                              f"be uploaded to the Wikidata item: "
                              f"{work.subject_qids}")
                # exit()
        return work

    def __parse_habanero_data__(self) -> Optional[CrossrefWork]:
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
                        if config.loglevel == logging.DEBUG:
                            logger.debug("Finished model dict")
                            console.print(work.dict())
                        print(work)
                        # references = work.reference
                        # if references is not None:
                        #     for reference in references:
                        #         if reference.first_page is not None:
                        #             int(reference.first_page)
                    # exit(0)
                    return work
            else:
                raise ValueError("type not found")

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
        if config.loglevel == logging.DEBUG:
            logger.debug("Here is the renamed dict")
            console.print(finished_data)
        self.data = finished_data
