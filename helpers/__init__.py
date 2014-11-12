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


free_license_urls = [
    'http://creativecommons.org/publicdomain/zero/1.0/'
]
for cc_license_type in ('by', 'by-sa'):
    for cc_version_number in ('2.0', '2.5', '3.0', '4.0'):
        cc_license_url = (
            "http://creativecommons.org/licenses/%s/%s" % (
                cc_license_type,
                cc_version_number,
                ))
        free_license_urls.append(cc_license_url)
        free_license_urls.append(cc_license_url + '/')

def is_free_license(url):
    """
    Return if a license is free as in freedom.

    >>> is_free_license('http://creativecommons.org/licenses/by-sa/2.5/')
    True

    >>> is_free_license('http://www.json.org/license.html')
    False

    """
    if url in free_license_urls:
        return True
    return False


if __name__ == "__main__":
    """Start doctests."""
    import doctest
    doctest.testmod()
