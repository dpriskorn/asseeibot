from enum import Enum, auto


class MatchStatus(Enum):
    """Models the 3 states of matching approved/declined/no_match
    The 2 former are stored in our MatchCache in a boolean.

    We could used a variable with True/False/None but
    this makes the code way more readable"""
    APPROVED = auto()
    DECLINED = auto()
    NO_MATCH = auto()
