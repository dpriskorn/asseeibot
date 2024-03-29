import logging

from pydantic.dataclasses import dataclass
from wikibaseintegrator import wbi_config

import config
from asseeibot.models.wikimedia.enums import WikidataNamespaceLetters

wbi_config.config['USER_AGENT'] = config.user_agent


@dataclass
class EntityId:
    raw_entity_id: str
    letter: WikidataNamespaceLetters = None
    # This can be e.g. "32698-F1" in the case of a lexeme
    rest: str = None

    # See https://pydantic-docs.helpmanual.io/usage/dataclasses/
    def __post_init_post_parse__(self):
        logger = logging.getLogger(__name__)
        if self.raw_entity_id is not None:
            # Remove prefix if found
            logger.debug("Removing prefixes")
            for prefix in config.wd_prefixes:
                if prefix in self.raw_entity_id:
                    self.raw_entity_id = self.raw_entity_id.replace(prefix, "")
            if len(self.raw_entity_id) > 1:
                logger.debug(f"entity_id:{self.raw_entity_id}")
                self.letter = WikidataNamespaceLetters(self.raw_entity_id[0:1])
                self.rest = self.raw_entity_id[1:]
            else:
                raise ValueError("Entity ID was too short.")
        else:
            raise ValueError("Entity ID was None")

    def url(self):
        return f"{config.wd_prefix}{str(self)}"

    def history_url(self):
        return f"https://www.wikidata.org/w/index.php?title={self.value}&action=history"

    @property
    def value(self):
        return f"{self.letter.value}{self.rest}"

    def __str__(self):
        return f"{self.letter.value}{self.rest}"

    # def extract_wdqs_json_entity_id(self, json: Dict, sparql_variable: str):
    #     self.__init__(json[sparql_variable]["value"].replace(
    #         config.wd_prefix, ""
    #     ))
