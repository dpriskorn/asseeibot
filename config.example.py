#!/usr/bin/env python3
import logging

# This file should be copied to config.py in the same directory

bot_username = ""
password = ""

# User settings
username = "So9q"  # This is good practice and used for the User-Agent.
# We thus send it to WMF every time we interact with the APIs

# NER settings
match_subjects_to_qids_and_upload = True  # For this to work you need to specify your credentials above
# These thresholds govern how close the 2 strings must be to match
# according to the https://en.wikipedia.org/wiki/Levenshtein_distance
alias_threshold_ratio: int = 85
label_threshold_ratio: int = 82

# General settings
exit_after_uploads_on_one_page = True
lookup_dois = True
ask_before_lookup = False
max_events = 0  # Max events to read. 0 = unlimited
missing_identitifier_limit = 2  # How many DOIs to stop after. 0 = unlimited
loglevel = logging.WARNING
cache_pickle_filename = "cache.pkl"
# excluded_wikis = ["ceb", "zh", "ja"]
# trust_url_file_endings = True

# These should not be altered by users:
version = "0.3-alpha1"
user_agent = f"Asynchronous Server Side Events External Identifier Bot/v{version} " \
             f"https://github.com/dpriskorn/asseeibot run by User:{username}"
wd_prefix = "http://www.wikidata.org/entity/"
wd_prefixes = ["http://www.wikidata.org/entity/", "https://www.wikidata.org/entity/",
               "https://www.wikidata.org/wiki/", "http://www.wikidata.org/wiki/"]

# These 2 variables are used to hold instances that we want to keep during the whole runtime
login_instance = None
ontology_dataframe = None
