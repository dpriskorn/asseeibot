#!/usr/bin/env python3
import json
import logging
from datetime import datetime
from os import path
from typing import List

from asseeibot import config

# Logging
logger = logging.getLogger(__name__)


def get_wikipedia_list():
    filename = config.wikipedia_list
    if path.isfile(filename):
        # Read the file
        with open(filename, 'r', encoding='utf-8') as myfile:
            string = myfile.read()
            if len(string) > 0:
                return json.loads(string)


def save_to_wikipedia_list(
        dois: List[str] = None,
        language_code: str = None,
        article: str = None,
        done: bool = False,
):
    """Only has side-effects."""
    filename = config.wikipedia_list
    if dois is None:
        logger.error("Error. DOIs was None")
    else:
        print(f"Adding {dois} to local list of DOIs found in Wikipedia")
        for doi in dois:
            data = dict(
                article=article,
                date=datetime.now().isoformat(),
                lang=language_code,
                done=done,
            )
            if path.isfile(filename):
                # Read the file
                with open(filename, 'r', encoding='utf-8') as myfile:
                    json_data = myfile.read()
                if len(json_data) > 0:
                    with open(filename, 'w', encoding='utf-8') as myfile:
                        # parse file
                        wikipedia_list = json.loads(json_data)
                        wikipedia_list[doi] = data
                        if config.debug_wikipedia_list:
                            logging.debug(f"dumping altered list:{wikipedia_list}")
                        json.dump(wikipedia_list, myfile, ensure_ascii=False)
                else:
                    logger.error("Error. JSON data had no entries. Remove the"+
                                 f" {filename} and try again.")
            else:
                # Create the file
                with open(filename, "w", encoding='utf-8') as outfile:
                    # Create new file with dict and item
                    wikipedia_list = {}
                    wikipedia_list[doi] = data
                    print(wikipedia_list)
                    if config.debug_wikipedia_list:
                        logging.debug(f"dumping:{wikipedia_list}")
                    json.dump(wikipedia_list, outfile, ensure_ascii=False) 
