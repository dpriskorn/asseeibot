import asyncio
import logging
from typing import List, Any
from urllib.parse import quote

import pywikibot
from aiohttp import ClientPayloadError
from aiosseclient import aiosseclient
from pywikibot import APISite

from asseeibot import config
from asseeibot.models.identifiers.doi import Doi
from asseeibot.models.pywikibot import PywikibotSite
from asseeibot.models.wikimedia.enums import WikimediaSite
from asseeibot.models.wikimedia.wikimedia_event import WikimediaEvent


class EventStream:
    """This models an event stream from WMF"""
    language_code: str = None
    pywikibot_site: PywikibotSite = None
    event_site: WikimediaSite = None
    # event_limit: int = 30
    missing_dois: List[Doi] = None
    missing_identitifier_limit: int = config.missing_identitifier_limit
    total_number_of_missing_dois: int = 0
    total_number_of_dois: int = 0
    total_number_of_missing_isbn: int = 0
    total_number_of_isbn: int = 0
    event_count: int = 0
    earlier_events: set = set(str)

    async def __get_events__(self):
        """Get events from the event stream until missing identifier limit"""
        logger = logging.getLogger(__name__)
        if not isinstance(self.missing_identitifier_limit, int) and self.missing_identitifier_limit > 0:
            raise ValueError("missing_identitifier_limit not an int or 0")
        self.pywikibot_site: APISite = self.__instantiate_pywikibot__()
        self.event_count = 0
        # We run in a while loop so we can continue even if we get a ClientPayloadError
        while True:
            try:
                async for event in aiosseclient(
                        'https://stream.wikimedia.org/v2/stream/recentchange',
                ):
                    wmf_event = WikimediaEvent(event=event,
                                               event_stream=self)
                    if wmf_event.page_title not in self.earlier_events:
                        wmf_event.process()
                        self.earlier_events.add(wmf_event.page_title)
                        if wmf_event.wikipedia_page is not None:
                            self.total_number_of_missing_dois += wmf_event.wikipedia_page.number_of_missing_dois
                            self.total_number_of_dois += wmf_event.wikipedia_page.number_of_dois
                            missing_dois = wmf_event.wikipedia_page.missing_dois
                            if missing_dois is not None and len(missing_dois) > 0:
                                self.missing_dois.extend(missing_dois)
                            self.__print_statistics__()
                            self.event_count += 1
                    else:
                        logger.info("Skipping page already processed earlier")
                    if (
                            self.total_number_of_missing_dois #+
                            #self.total_number_of_missing_isbn
                    ) >= self.missing_identitifier_limit:
                        print(f"Reached missing identifier limit of {self.missing_identitifier_limit}. Exiting")
                        self.__print_missing_dois__()
                        self.__print_sourcemd_link__()
                        exit(0)
                    if config.max_events > 0 and self.event_count == config.max_events:
                        exit(0)
            except ClientPayloadError:
                logger.error("ClientPayloadError")
                continue
            if config.max_events > 0 and self.event_count == config.max_events:
                exit(0)

    def __init__(self,
                 language_code: str = None,
                 event_site: WikimediaSite = None
                 ):
        if language_code is None or event_site is None:
            raise ValueError("did not get what we need")
        self.language_code = language_code
        self.event_site = event_site
        self.missing_dois = []
        self.__instantiate_pywikibot__()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__get_events__())

    def __instantiate_pywikibot__(self):
        return pywikibot.Site(self.language_code, 'wikipedia')

    def __print_missing_dois__(self):
        for doi in self.missing_dois:
            print(doi)

    def __print_sourcemd_link__(self):
        quoted_newline = quote("\r\n")
        doi_string = quoted_newline.join([str(doi) for doi in self.missing_dois])
        print(f"https://sourcemd.toolforge.org/index_old.php?id={doi_string}&doit=Check+source")

    def __print_statistics__(self):
        if self.total_number_of_dois > 0:
            percentage = int(round(self.total_number_of_missing_dois * 100 / self.total_number_of_dois, 0))
        else:
            percentage = 0
        print(f"Processed {self.event_count} events and found {self.total_number_of_dois}" +
              f" DOIs. {self.total_number_of_missing_dois} "
              f"({percentage}%) "
              f"are missing in WD.")
