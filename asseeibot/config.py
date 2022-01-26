#!/usr/bin/env python3

# Default is list-mode where we collect all DOIs found but do nothing else
import logging

import_mode = False
lookup_dois = True
ask_before_lookup = False
# Max events to read. 0 = unlimited
max_events = 0
username = "So9q"
loglevel = logging.WARNING

version = "0.2-alpha0"
user_agent = f"Asynchronous Server Side Events External Identifier Bot/v{version} " \
           f"https://github.com/dpriskorn/asseeibot run by User:{username}"
wikipedia_list = "found_in_wikipedia.json"
wd_prefix = "http://www.wikidata.org/entity/"

# Debug
debug_wikipedia_list = False
