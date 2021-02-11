#!/usr/bin/env python3
import os
from datetime import datetime, timezone
import json
import logging

import config
import loglevel

# Logging
logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    logger.debug("Setting loglevel in config")
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("io.log")
logger.addHandler(file_handler)

def save_to_wikipedia_list(
        dois: List[str] = None,
        language_code: str = None,
        article: str = None
):
    """Only has side-effects."""
    if dois is None:
        logger.error("Error. DOIs was None")
    else:
        print(f"Adding {dois} to local list of DOIs found in Wikipedia")
        for doi in dois:
            data = dict(
                article=article,
                date=datetime.now().isoformat(),
                lang=config.language_code,
            )
            if os.path.isfile(config.wikipedia_list):
                # Read the file
                with open(config.wikipedia_list, 'r', encoding='utf-8') as myfile:
                    json_data = myfile.read()
                if len(json_data) > 0:
                    with open(config.wikipedia_list, 'w', encoding='utf-8') as myfile:
                        # parse file
                        wikipedia_list = json.loads(json_data)
                        wikipedia_list[doi] = data
                        if config.debug_wikipedia_list:
                            logging.debug(f"dumping altered list:{wikipedia_list}")
                        json.dump(wikipedia_list, myfile, ensure_ascii=False)
                else:
                    logger.error("Error. JSON data had no entries. Remove the"+
                                 f" {config.wikipedia_list} and try again.")
            else:
                # Create the file
                with open(config.wikipedia_list, "w", encoding='utf-8') as outfile:
                    # Create new file with dict and item
                    wikipedia_list = {}
                    wikipedia_list[form_id] = form_data
                    if config.debug_wikipedia_list:
                        logging.debug(f"dumping:{wikipedia_list}")
                    json.dump(wikipedia_list, outfile, ensure_ascii=False) 
