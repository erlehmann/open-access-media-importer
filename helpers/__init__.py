from autovividict import autovividict
from urllib2 import quote


def make_datestring(year, month=None, day=None):
    """
    Return a date string constructed from given year, month, day.

    Year, months and day must have type int.
    The result of this function has type str.

    Result has form YYYY if only year is given.

    >>> make_datestring(1987)
    '1987'

    Result has form YYYY-MM if year and month are given.

    >>> make_datestring(1987, 10)
    '1987-10'

    Result has form YYYY-MM-DD if year, month and day are given.

    >>> make_datestring(1987, 10, 10)
    '1987-10-10'
    """

    datestring = "%04d" % year  # YYYY
    if month is not None:
        datestring += "-%02d" % month  # YYYY-MM
    if day is not None:
        datestring += "-%02d" % day  # YYYY-MM-DD
    return datestring


def filename_from_url(url):
    """
    Quote all characters in URL that are forbidden in a file system.

    >>> filename_from_url('http://example.org/123#%23')
    'http%3A%2F%2Fexample.org%2F123%23%2523'
    """
    return quote(url, safe='')


if __name__ == "__main__":
    """Start doctests."""
    import doctest
    doctest.testmod()
