#!/usr/bin/env python
# -*- coding: utf-8 -*-

from autovividict import autovividict
from urllib2 import quote


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
