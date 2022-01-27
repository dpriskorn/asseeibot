class Identifier:
    """Base model for an identifier"""
    string: str = None

    def __str__(self):
        return self.string
