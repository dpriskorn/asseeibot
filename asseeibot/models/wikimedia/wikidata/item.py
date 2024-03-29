from typing import Optional, List

from pydantic import BaseModel
from wikibaseintegrator import wbi_config, WikibaseIntegrator
from wikibaseintegrator.entities import Item as EntityItem
from wikibaseintegrator.wbi_helpers import search_entities

import config
from asseeibot.models.wikimedia.enums import WikimediaLanguage


class Item(BaseModel):
    qid: str
    __item: Optional[EntityItem]
    __aliases: Optional[List[str]]
    __description: Optional[str]

    def __fetch__(self):
        # fetch using WBI
        wbi_config.config["USER_AGENT_DEFAULT"] = config.user_agent
        wbi = WikibaseIntegrator(login=None)
        self.__item = wbi.item.get()

    @property
    def aliases(self):
        if self.__item is None:
            self.__fetch__()
        if self.__aliases is None:
            self.__aliases = self.__item.aliases.get(WikimediaLanguage.ENGLISH.value)
        return self.__aliases

    @property
    def description(self):
        if self.__item is None:
            self.__fetch__()
        if self.__description is None:
            self.__description = self.__item.descriptions.get(WikimediaLanguage.ENGLISH.value)
        return self.__description

    @staticmethod
    def __call_wbi_search_entities__(subject):
        return search_entities(search_string=subject,
                               language="en",
                               dict_result=True,
                               max_results=1)
