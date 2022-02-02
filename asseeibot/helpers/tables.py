from typing import List

from rich.table import Table

from asseeibot import console
from asseeibot.models.crossref.work import CrossrefWork
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.wikimedia.wikipedia.wikipedia_page import WikipediaPage


def print_match_table(crossref_work: CrossrefWork):
    table = Table(title="Matches approved by you or from your previous choices")
    table.add_column(f"Q-item")
    table.add_column(f"Label")
    table.add_column(f"Alias")
    table.add_column(f"==")
    table.add_column(f"Crossref subject")
    # show QID URL in a column?
    for match in crossref_work.ner.subject_matches:
        table.add_row(match.qid.value, match.label, match.alias, "==", match.original_subject)
    console.print(table)


def print_all_matches_table(wikipedia_page: WikipediaPage):
    table = Table(title="Matches approved by you or from your previous choices")
    table.add_column(f"Q-item")
    table.add_column(f"Label")
    table.add_column(f"Alias")
    table.add_column(f"==")
    table.add_column(f"Crossref subject")
    # show QID URL in a column?
    matches = []
    matches_lists: List[List[FuzzyMatch]] = [doi.crossref.work.ner.subject_matches for doi in wikipedia_page.dois
                                             if doi.crossref.work.ner is not None]
    for match_list in matches_lists:
        matches.extend(match_list)
    for match in matches:
        table.add_row(match.qid.value, match.label, match.alias, "==", match.original_subject)
    console.print(table)