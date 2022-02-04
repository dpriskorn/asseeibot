#!/usr/bin/env python3
import logging
from typing import Any

from aiosseclient import aiosseclient  # type: ignore

import config
from asseeibot.helpers.argparse_setup import setup_argparse_and_return_args
from asseeibot.helpers.console import console
from asseeibot.models.crossref_engine.ontology_based_ner_matcher import FuzzyMatch
from asseeibot.models.pickled_dataframe.matches import Matches
from asseeibot.models.wikimedia.enums import WikimediaSite
from asseeibot.models.wikimedia.event_stream import EventStream
from asseeibot.models.wikimedia.wikidata.entity_id import EntityId

logging.basicConfig(level=config.loglevel)


def delete_match(args: Any):
    qid = EntityId(args.delete_match)
    console.print(f"Deleting match '{qid.value}' now")
    cache = Matches(match=FuzzyMatch(qid=qid))
    if cache.delete():
        console.print("Match deleted")
    else:
        console.print("Match not found")


def main():
    # logger = logging.getLogger(__name__)
    # print("Running main")
    args = setup_argparse_and_return_args()
    if config.loglevel == logging.DEBUG:
        console.print(args)
    if args.delete_match:
        delete_match(args)
    else:
        console.print("Looking for new DOIs from the WikimediaEvent stream")
        # We support only the English Wikipedia for now
        EventStream(language_code="en", event_site=WikimediaSite.WIKIPEDIA)
