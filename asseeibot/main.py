#!/usr/bin/env python3
import asyncio
import json
import logging
from urllib.parse import quote

import pywikibot
from aiosseclient import aiosseclient  # type: ignore
from rich import print

import config
import input_output
import wikidata

logging.basicConfig(level=logging.INFO)

# wikidata.lookup_issn("2535-7492")
# exit(0)

doi_prefixes = ["https://doi.org/", "http://doi.org/",
                "http://citeseerx.ist.psu.edu/viewdoc/summary?doi=",
                "http://www.tandfonline.com/doi/abs/",
                "https://dx.doi.org/"]
excluded_wikis = ["ceb", "zh", "ja"]
wd_prefix = "http://www.wikidata.org/entity/"
trust_url_file_endings = True


def check_if_done(doi):
    """Checks whether the doi has has already been imported by this bot"""
    data = input_output.get_wikipedia_list()
    if data is not None:
        for item in data:
            if item == doi:
                return True
    # This is only reached if no match
    return False


def finish_all_in_list():
    print("Going through the local list of found DOIs and finishing importing them all")
    data = input_output.get_wikipedia_list()
    dois = []
    if data is not None:
        # print(data)
        for doi in data:
            if data[doi]["done"] is False:
                dois.append(doi)
        if len(dois) > 0:
            wikidata.lookup_dois(dois=dois, in_wikipedia=True)
        print("Done")


def process_event(
        site,
        language_code=None,
        title=None,
):
    logger = logging.getLogger(__name__)
    # TODO flesh out the finding of cite journal and
    #  create an OOP model for it
    page = pywikibot.Page(site, title)
    raw = page.raw_extracted_templates
    dois = set()
    for template_name, content in raw:
        # print(f"working on {template_name}")
        if template_name.lower() == "cite journal":
            print(f"content:{content}")
            journal = None
            doi = None
            jstor = None
            pmid = None
            article_title = None
            for key, value in content.items():
                if key == "doi":
                    logger.info(f"Found doi: {value}")
                    doi = value
                    dois.add(doi)
                if key == "journal":
                    logger.info(f"Found journal: {value}")
                    journal = value
                if key == "jstor":
                    logger.info(f"Found jstor: {value}")
                    jstor = value
                if key == "pmid":
                    logger.info(f"Found pmid: {value}")
                    pmid = value
                if key == "title":
                    logger.info(f"Found title: {value}")
                    article_title = value
            if doi is None:
                logger.warning(f"An article titled {article_title} in the journal {journal} was found but no DOI. "
                               f"pmid:{pmid} jstor:{jstor}")
    missing_dois = []
    if config.import_mode:
        # Remove the DOIs that are marked done locally
        if dois is not None and len(dois) > 0:
            for doi in dois:
                done = check_if_done(doi)
                if done:
                    dois.remove(doi)
                    logger.info(f"{doi} has been found before.")
    if len(dois) > 0:
        if config.ask_before_lookup:
            input('Press enter to continue: ')
        missing_dois = wikidata.lookup_dois(dois=dois, in_wikipedia=True)
        if missing_dois is not None and len(missing_dois) > 0:
            input_output.save_to_wikipedia_list(missing_dois, language_code, title)
        # if config.import_mode:
        # answer = util.yes_no_question(
        #     f"{doi} is missing in WD. Do you"+
        #     " want to add it now?"
        # )
        # if answer:
        #     crossref.lookup_data(doi=doi, in_wikipedia=True)
        #     pass
        # else:
        #     pass
    # Return tuple with counts
    return len(dois), len(missing_dois)


async def main():
    print("Running main")
    if config.import_mode:
        finish_all_in_list()
    print("Looking for new DOIs from the Event stream")
    # We support only the English Wikipedia for now
    site = pywikibot.Site('en', 'wikipedia')
    count = 0
    count_dois_found = 0
    count_missing_dois = 0
    async for event in aiosseclient(
            'https://stream.wikimedia.org/v2/stream/recentchange',
    ):
        logger = logging.getLogger(__name__)
        # print(event)
        data = json.loads(str(event))
        # print(data)
        # meta = data["meta"]
        # what is the difference?
        server_name = data['server_name']
        namespace = int(data['namespace'])
        language_code = server_name.replace(".wikipedia.org", "")
        # for exclude in excluded_wikis:
        # if language_code == exclude:
        if language_code != "en":
            continue
        if server_name.find("wikipedia") != -1 and namespace == 0:
            title = data['title']
            if data['bot'] is True:
                bot = "(bot)"
            else:
                bot = "(!bot)"
            if data['type'] == "new":
                type = "(new)"
            elif data['type'] == "edit":
                type = "(edit)"
            else:
                type = None
            if type is not None:
                logger.info(f"{type}\t{server_name}\t{bot}\t\"{title}\"")
                logger.info(f"http://{server_name}/wiki/{quote(title)}")
                dois_count_tuple = process_event(
                    site,
                    # language_code=language_code,
                    title=title,
                )
                if dois_count_tuple[0] > 0:
                    count_dois_found += dois_count_tuple[0]
                if dois_count_tuple[1] > 0:
                    count_missing_dois += dois_count_tuple[1]
                count += 1
                print(f"Processed {count} events and found {count_dois_found}" +
                      f" DOIs where {count_missing_dois} were missing in WD.")
    if config.max_events > 0 and count == config.max_events:
        exit(0)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

# debug
# input_output.save_to_wikipedia_list(["doi"], "en", "title")
# exit(0)

# def search_isbn(page):
#     content = page.content
#     # TODO search for isbns
#     #             found = True
#     #             isbns.append(isbn)
#     #             print(
#     #                 f"{found_text}{doi}",
#     #             )
#     #     if found:
#     #         lookup_isbn(isbns)
#     #         sleep(1)
#     # else:
#     #     print("ISBN number not found")


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
#                         # e.g. 10.1525/aa.1965.67.5.02a00560/asset/aa.1965.67.5.02a00560.pdf;jsessionid=F9912E4EA20516C07E35701700EEBE71.f04t01?v=1&t=hoovxr8v&s=91fed24eb577
#                         # 9c1f45a2e1729d1dc3e0bf734fab
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
