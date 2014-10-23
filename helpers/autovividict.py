from collections import defaultdict

class countdict(defaultdict):
    """
    Dictionary that serves as neutral element for addition (0).

    >>> c = countdict()
    >>> c['k'] = 'v'
    >>> c
    {'k': 'v'}
    >>> c + 1
    1

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

    Unknown keys serve as neutral element for addition (0).

    >>> a = autovividict()
    >>> a['k0'] = 'abc'
    >>> a['k1'] += 1111
    >>> a['k2']['k20'] = 'def'
    >>> a['k2']['k21'] += 2222
    >>> a
    {'k2': {'k20': 'def', 'k21': 2222}, 'k1': 1111, 'k0': 'abc'}

    """
    return countdict(autovividict)


if __name__ == '__main__':
    """Start doctests."""
    import doctest
    doctest.testmod()
