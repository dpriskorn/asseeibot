#!/usr/bin/env python3
import asyncio
import json
import requests
from time import sleep

import aiohttp
from aiosseclient import aiosseclient # type: ignore
from mediawikiapi import MediaWikiAPI, PageError # type: ignore
from rich import print

doi_prefix = "https://doi.org/"
excluded_wikis = ["ceb", "zh", "ja"]
mediawikiapi = MediaWikiAPI()
found_text = "[bold red]DOI link found:[/bold red] "

def search_doi(page):
    # Look for doi links
    links = page.references  # broken because of bug
    if links is not None:
        #print(f"References:{links}")
        found = False
        for link in links:
            if link.find(doi_prefix) != -1:
                found = True
                print(
                    f"{found_text}{link.replace(doi_prefix, '')} ",
                )
        if found:
            sleep(1)
    else:
        print("External links not found")

def download_page(
        language_code: str = None,
        title: str = None,
):
    print("Downloading wikitext")
    mediawikiapi.config.language = language_code
    #print(mediawikiapi.summary(title, sentences=1))
    page = False
    try:
        page = mediawikiapi.page(title)
    except PageError:
        print("Got page error, skipping")
    if page:
        print("Download finished")
        #print(page.sections)
        search_doi(page)
        #print("Looking for templates")

async def main():
    async for event in aiosseclient(
            'https://stream.wikimedia.org/v2/stream/recentchange',
    ):
        #print(event)
        data = json.loads(str(event))
        #print(data)
        meta = data["meta"]
        # what is the difference?
        server_name = data['server_name']
        namespace = int(data['namespace'])
        language_code = server_name.replace(".wikipedia.org", "")
        # for exclude in excluded_wikis:
            #if language_code == exclude:
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
                print(f"{type}\t{server_name}\t{bot}\t'{title}'")
                print(f"http://{server_name}/wiki/{title.replace(' ', '_')}")
                download_page(
                    language_code=language_code,
                    title=title,
                )

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
