import json
import logging
from typing import Any, Dict
from urllib.parse import quote

from asseeibot.models.wikimedia.enums import WikimediaEditType
from asseeibot.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage


class WikimediaEvent:
    """This models a WMF kafka event from the EventStream API"""
    bot_edit: bool
    edit_type: WikimediaEditType = None
    event_data: Dict[str, str] = None
    event_stream: Any = None  # We can't type this because of pydantic
    language_code: str = None
    namespace: int = None
    page_title: str = None
    server_name: str = None
    wikipedia_page: WikipediaPage = None

    def __init__(self, event: Any = None,
                 event_stream: Any = None):
        if event is None:
            raise ValueError("event was None")
        self.event_data = json.loads(str(event))
        if self.event_data is None:
            raise ValueError(f"got None after parsing the event {event} to json")
        self.event_stream = event_stream
        if self.event_stream.event_site is None:
            raise ValueError("got no site")
        if self.event_stream.language_code is None:
            raise ValueError("got no language code")
        self.__parse__()

    def __parse__(self):
        # meta = data["meta"]
        self.server_name = self.event_data['server_name']
        self.namespace = int(self.event_data['namespace'])
        self.language_code = self.server_name.replace(f".{self.event_stream.event_site.value}.org", "")
        self.page_title = self.event_data['title']
        self.bot_edit = bool(self.event_data['bot'])
        self.edit_type = WikimediaEditType(self.event_data['type'])

    def __print_progress__(self):
        logger = logging.getLogger(__name__)
        if self.edit_type is not None:
            if self.bot_edit is True:
                bot = "(bot)"
            else:
                bot = "(!bot)"
            logger.info(f"Working on '{self.page_title}'")
            logger.info(f"({self.edit_type.value})\t{self.server_name}\t{bot}\t\"{self.url()}\"")

    def process(self):
        logger = logging.getLogger(__name__)
        if self.language_code != "en":
            return
        # We only want the article namespace (0)
        if self.server_name.find(self.event_stream.event_site.value) != -1 and self.namespace == 0:
            logger.info("Found enwp article edit")
            self.__print_progress__()
            self.wikipedia_page = WikipediaPage(wikimedia_event=self)
            self.wikipedia_page.start()
        else:
            logger.debug(f"Skipping event from {self.server_name}")

    def url(self):
        return f"http://{self.server_name}/wiki/{quote(self.page_title)}"

