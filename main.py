#!/usr/bin/env python3
import asyncio
import json
import requests
from time import sleep

import aiohttp
from aiosseclient import aiosseclient # type: ignore
from mediawikiapi import MediaWikiAPI # type: ignore

doi_prefix = "https://doi.org/"
excluded_wikis = ["ceb", "zh", "ja"]

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
        for exclude in excluded_wikis:
            if server_name.find(exclude) == -1:
                continue
        if server_name.find("wikipedia") != -1 and namespace == 0:
            language_code = server_name.replace(".wikipedia.org", "")
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
            if type is not None and language_code == "en":
                print(f"{type}\t{server_name}\t{bot}\t'{title}'")
                print(f"http://{server_name}/wiki/{title.replace(' ', '_')}")
                print("Downloading wikitext")
                mediawikiapi = MediaWikiAPI()
                mediawikiapi.config.language = language_code
                #print(mediawikiapi.summary(title, sentences=1))
                try:
                    page = mediawikiapi.page(title)
                except mediawikiapi.exceptions.PageError:
                    print("Got page error, skipping")
                if page:
                    print("Download finished")
                    print(page.sections)
                    if language_code == "en":
                        #print("enwiki detected")
                        # Look for doi links
                        links = page.references
                        if links is not None:
                            print(f"References:{links}")
                            for link in links:
                                if link.find(doi_prefix) != -1:
                                    print(
                                        "DOI link found: {link.replace(doi_prefix, '')} ",
                                    )
                        else:
                            print("External links not found")
                    # print(page.content.find("DOI"))
                    # print(page.content.find("DOI:"))
                    # print(page.content.find("doi="))
                    #print("Looking for templates")
            sleep(2)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
