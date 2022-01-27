from asseeibot.models.identifier import Identifier


class Doi(Identifier):
    """Models a DOI"""

    def __init__(self, value):
        if value is None:
            raise ValueError("value was None")
        # todo test it with a regex on init
        self.string = value

    def __str__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.string.upper()

    def __repr__(self):
        """DOI identifiers are case-insensitive.
        Return upper case always to make sure we
        can easily look them up via SPARQL later"""
        return self.string.upper()
