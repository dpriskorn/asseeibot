#!/usr/bin/env python3
import logging

from aiosseclient import aiosseclient  # type: ignore
from rich import print

import config
from asseeibot.models.wikimedia.enums import WikimediaSite
from asseeibot.models.wikimedia.event_stream import EventStream

logging.basicConfig(level=config.loglevel)


def main():
    # logger = logging.getLogger(__name__)
    # print("Running main")
    print("Looking for new DOIs from the WikimediaEvent stream")
    # We support only the English Wikipedia for now
    EventStream(language_code="en", event_site=WikimediaSite.WIKIPEDIA)
    # TODO model a Wikicitations Page and enable enriching it using WBI

# def old_search_doi(page) -> Optional[List[str]]:
#     logger = logging.getLogger(__name__)
#     links = page.references
#     if links is not None:
#         logger.debug(f"References:{links}")
#         found = False
#         dois = set()
#         # This should catch >99% of all DOIs
#         # but it seems it does not...
#         # doi_regex_pattern = "/^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i"
#         # This is my simplified pattern
#         doi_regex_pattern = "10.\d{4,9}\/+.+"
#         for link in links:
#             # We unquote to avoid the URL garbage like %A1
#             match = re.search(doi_regex_pattern, unquote(link))
#             if match is not None:
#                 found_excluded_word = False
#                 doi = match.group()
#                 excluded_words = [
#                     "/ww-",  # whoswho
#                     "http", ".pdf", "jsessionid", "htm", "jpg", "png"
#                 ]
#                 for word in excluded_words:
#                     if word in doi:
#                         found_excluded_word = True
#                         # This is probably a fulltext url, so we skip it
#                 if not found_excluded_word:
#                     found = True
#                     dois.add(doi)
#                     logger.info(f"found DOI via regex: {doi}")
#             for doi_prefix in doi_prefixes:
#                 if link.find(doi_prefix) != -1:
#                     # unquote to convert %2F -> /
#                     doi = unquote(link.replace(doi_prefix, ''))
#                     if doi not in dois:
#                         found = True
#                         dois.add(doi)
#                         found_text = "[bold red]DOI link found via prefix, but not the regex:[/bold red] "
#                         print(f"{found_text}{doi}")
#                         print(match)
#                         exit()
#             if link.find("doi") != -1:
#                 known_prefix = False
#                 for doi_prefix in doi_prefixes:
#                     if link.find(doi_prefix) != -1:
#                         known_prefix = True
#                 if not known_prefix:
#                     print(f"new doi prefix found: {link}")
#                     # exit()
#         if found:
#             logger.debug(f"found the following dois")
#             pprint(dois)
#             # exit()
#             return dois
#         else:
#             print("External links not found")
#             return None
#     else:
#         print("External links not found")
#         return None


# def download_page(
#         mediawikiapi: MediaWikiAPI,
#         language_code: str = None,
#         title: str = None,
# ):
#     logger = logging.getLogger(__name__)
#     logger.info("Downloading wikitext")
#     mediawikiapi.config.language = language_code
#     # print(mediawikiapi.summary(title, sentences=1))
#     page = False
#     try:
#         page = mediawikiapi.page(title=title, auto_suggest=False)
#         if page is not None:
#             logger.info("Download finished")
#             return page
#         else:
#             return None
#     except PageError:
#         logger.warning("Got page error, skipping")
#         return None
#     # print(page.sections)
#     # print("Looking for templates")
