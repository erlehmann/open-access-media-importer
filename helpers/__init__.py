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


def add_verbose_option(parser):
    """
    Add verbosity option to an argparse.ArgumentParser parser.

    >>> from argparse import ArgumentParser
    >>> parser = ArgumentParser()
    >>> parser = add_verbose_option(parser)

    No “-v” argument spcifies a verbosity level of zero.

    >>> parser.parse_args([])
    Namespace(verbose=0)

    One “-v” option specifies a verbosity level of one.

    >>> parser.parse_args(['-v'])
    Namespace(verbose=1)

    Multiple “-v” options specify higher verbosity level.

    >>> parser.parse_args(['-vvv'])
    Namespace(verbose=3)
    """
    parser.add_argument(
        '-v',
        '--verbose',
        help='Increase verbosity.',
        action='count',
        default=0,
        )
    return parser


def init_logging(verbose):
    """
    Initialize logging according to verbosity level. If a logged
    message's logging level is higher than the specified logging
    level, it will not be printed.

    The following python code prints “WARNING: dummy warning”, but
    does not print “INFO: dummy info”.

    logging = init_logging(1)
    logging.info('dummy info')
    logging.warning('dummy warning')
    """
    # FIXME: This function has no doctest because logging and doctest
    # do not play well with each other. I have no idea how to fix it.

    import logging
    if verbose == 0:
        loglevel = logging.ERROR
    if verbose == 1:
        loglevel = logging.WARN
    if verbose == 2:
        loglevel = logging.INFO
    if verbose == 3:
        loglevel = logging.DEBUG

    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=loglevel
        )
    return logging


if __name__ == "__main__":
    """Start doctests."""
    import doctest
    doctest.testmod()
