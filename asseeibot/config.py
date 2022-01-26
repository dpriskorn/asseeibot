#!/usr/bin/env python3

# Default is list-mode where we collect all DOIs found but do nothing else 
import_mode = False
lookup_dois = True

# Max events to read. 0 = unlimited
max_events = 0

loglevel = None
wikipedia_list = "found_in_wikipedia.json"
wd_prefix = "http://www.wikidata.org/entity/"

# Debug
debug_wikipedia_list = True
