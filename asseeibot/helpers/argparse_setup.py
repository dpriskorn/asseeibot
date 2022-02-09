import argparse
from typing import Optional

from tap import Tap


class ArgumentParser(Tap):
    delete_match: Optional[str] = None  # "Delete a match from your local cache of earlier matches."


def setup_argparse_and_return_args():
    parser = ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                            description="""
Asseeibot enables working main subject statements on items based on a 
heuristic matching the subjects on works in CrossrefEngine with a custom domain specific ontology. 

It caches all matches for later reuse.

You can delete a match from the cache if you accidentally made a mistake or later regret your decision.

NOTE: we do not yet support removing statements from Wikidata based on the bad match.
    """)
    return parser.parse_args()
