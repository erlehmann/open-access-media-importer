from collections import defaultdict

class countdict(defaultdict):
    """
    Dictionary that serves as neutral element (0) for addition.

    This dictionary allows incrementing unknown keys: d['k'] += 1
    """
    def __init__(self, *args, **kwargs):
        self.value = 0
        super(countdict, self).__init__(*args, **kwargs)
    def __repr__(self):
        return str(dict(self))
    def __add__(self, x):
        return self.value + x

def autovividict():
    """
    Autovivicatious counting dictionary, allowing dynamic creation of keys.

    Autovivication is the automatic creation of new dictionaries as
    required when an undefined value is dereferenced. Explanation:
    <http://en.wikipedia.org/wiki/Autovivification#Python>
    """
    return countdict(autovividict)
