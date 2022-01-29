from rich.console import Console
from rich.table import Table

from asseeibot.models.crossref.work import CrossrefWork

console = Console()


def print_match_table(crossref_work: CrossrefWork):
    table = Table(title="Matches approved by you or from your previous choices")
    table.add_column(f"Q-item")
    table.add_column(f"Label")
    table.add_column(f"==")
    table.add_column(f"Crossref subject")
    for match in crossref_work.ner.subject_matches:
        table.add_row(match.qid.value, match.label, "==", match.original_subject)
    console.print(table)

