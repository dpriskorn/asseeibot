#!/usr/bin/env python3
import logging

username = "So9q@descriptionerbot"
password = "7f5uivo395t30bfgjvrduvbtumts3equ"

# User settings
username = "So9q"  # This is good practice and used for the User-Agent.
                   # We thus send it to WMF every time we interact with the APIs
lookup_dois = True
ask_before_lookup = False
max_events = 0  # Max events to read. 0 = unlimited
missing_identitifier_limit = 15  # How many DOIs to stop after. 0 = unlimited
loglevel = logging.WARNING
match_subjects_to_qids_and_upload = True  # For this to work you need to specify your credentials above
cache_pickle_filename = "cache.pkl"
# excluded_wikis = ["ceb", "zh", "ja"]
# trust_url_file_endings = True

# These should not be altered by users:
version = "0.2-alpha0"
user_agent = f"Asynchronous Server Side Events External Identifier Bot/v{version} " \
           f"https://github.com/dpriskorn/asseeibot run by User:{username}"
wd_prefix = "http://www.wikidata.org/entity/"
login_instance = None