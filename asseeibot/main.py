#!/usr/bin/env python3
import asyncio
import json
import logging
from time import sleep
from urllib.parse import quote, unquote

import aiohttp
from aiosseclient import aiosseclient # type: ignore
from mediawikiapi import MediaWikiAPI, PageError # type: ignore
from rich import print
from typing import List, Union, Dict, Optional

import config
import input_output
import wikidata

# wikidata.lookup_issn("2535-7492")
# exit(0)

doi_prefix = "https://doi.org/"
excluded_wikis = ["ceb", "zh", "ja"]
found_text = "[bold red]DOI link found:[/bold red] "
wd_prefix = "http://www.wikidata.org/entity/"
trust_url_file_endings = True

# debug
# input_output.save_to_wikipedia_list(["doi"], "en", "title")
# exit(0)

def search_isbn(page):
    content = page.content
    # TODO search for isbns
    #             found = True
    #             isbns.append(isbn)
    #             print(
    #                 f"{found_text}{doi}",
    #             )
    #     if found:
    #         lookup_isbn(isbns)
    #         sleep(1)
    # else:
    #     print("ISBN number not found")


def search_doi(page) -> Optional[List[str]]:
    links = page.references
    if links is not None:
        #print(f"References:{links}")
        found = False
        dois = []
        for link in links:
            if link.find(doi_prefix) != -1:
                found = True
                # unquote to convert %2F -> /
                doi = unquote(link.replace(doi_prefix, ''))
                dois.append(doi)
                print(
                    f"{found_text}{doi}",
                )
        if found:
            return dois
        else:
            print("External links not found")
            return None
    else:
        print("External links not found")
        return None


def download_page(
        mediawikiapi,
        language_code: str = None,
        title: str = None,
):
    print("Downloading wikitext")
    mediawikiapi.config.language = language_code
    #print(mediawikiapi.summary(title, sentences=1))
    page = False
    try:
        page = mediawikiapi.page(title)
        success = True
        if page is not None:
            print("Download finished")
            return page
        else:
            return None
    except PageError:
        print("Got page error, skipping")
        success = False
        return None
    #print(page.sections)
    #print("Looking for templates")


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
    data = None
    data = input_output.get_wikipedia_list()
    dois = []
    if data is not None:
        # print(data)
        for doi in data:
            if data[doi]["done"] is False:
                dois.append(doi)
        if len(dois) >0:
            wikidata.lookup_dois(dois=dois, in_wikipedia=True)
        print("Done")


def process_event(
        mediawikiapi,
        language_code=None,
        title=None,
):
    page = download_page(
        mediawikiapi,
        language_code=language_code,
        title=title,
    )
    dois = None
    missing_dois = None
    if page is not None:
        dois = search_doi(page)
        if dois is not None and len(dois) > 0:
            for doi in dois:
                done = check_if_done(doi)
                if done:
                    dois.remove(doi)
                    print(f"{doi} has been found before.")
        if dois is not None and not done:
            #input('Press enter to continue: ')
            missing_dois = wikidata.lookup_dois(dois=dois, in_wikipedia=True)
            if len(missing_dois) > 0:
                input_output.save_to_wikipedia_list(missing_dois, language_code, title)
            #if config.import_mode:
                # answer = util.yes_no_question(
                #     f"{doi} is missing in WD. Do you"+
                #     " want to add it now?"
                # )
                # if answer:
                #     crossref.lookup_data(doi=doi, in_wikipedia=True)
                #     pass
                # else:
                #     pass
        else:
            pass
    # Return tuple with counts
    if dois is not None and missing_dois is None:
        return (len(dois), 0)
    elif dois is None and missing_dois is not None:
        return (len(dois),len(missing_dois))
    elif dois is not None and missing_dois is not None:
        return (len(dois),len(missing_dois))
    else:
        return (0,0)


async def main():
    print("Running main")
    if config.import_mode:
        finish_all_in_list()
    print("Looking for new DOIs from the Event stream")
    mediawikiapi = MediaWikiAPI()
    count = 0
    count_dois_found = 0
    count_missing_dois = 0
    async for event in aiosseclient(
            'https://stream.wikimedia.org/v2/stream/recentchange',
    ):
        # print(event)
        data = json.loads(str(event))
        # print(data)
        meta = data["meta"]
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
                print(f"{type}\t{server_name}\t{bot}\t\"{title}\"")
                print(f"http://{server_name}/wiki/{quote(title)}")
                dois_count_tuple = process_event(
                    mediawikiapi,
                    language_code=language_code,
                    title=title,
                )
                if dois_count_tuple[0] > 0:
                    count_dois_found += dois_count_tuple[0]
                if dois_count_tuple[1] > 0:
                    count_missing_dois += dois_count_tuple[1]
                count += 1
                print(f"Processed {count} events and found {count_dois_found}"+
                      f" DOIs where {count_missing_dois} were missing in WD.")
    if config.max_events > 0 and count == config.max_events:
        exit(0)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
