#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib2 import urlopen, urlparse, Request, HTTPError
from xml.etree.cElementTree import dump, ElementTree
from sys import stderr

def _get_file_from_url(url):
    """
    Download file from a given URL.

    >>> f = _get_file_from_url('http://example.org')
    >>> 'Example Domain' in f.read()
    True

    """
    req = Request(url, None, {'User-Agent' : 'oa-put/2012-08-15'})
    try:
        remote_file = urlopen(req)
        return remote_file
    except HTTPError as e:
        stderr.write('When trying to download <%s>, the following error occured: “%s”.\n' % \
            (url, str(e)))
        exit(255)

def get_pmcid_from_doi(doi):
    """
    Return PMCID of a document that has the given DOI.

    The input value of this function must have type “unicode”.
    The return value of this function has the type of “int”.

    >>> get_pmcid_from_doi(u'10.1371/journal.pone.0062199')
    3631234
    >>> get_pmcid_from_doi(u'10.1371/journal.pone.0093036')
    3973673
    >>> get_pmcid_from_doi(u'10.1371/journal.pone.0099936')
    4057317

    >>> get_pmcid_from_doi('10.1371/journal.pone.0062199')
    Traceback (most recent call last):
      ...
    TypeError: Cannot get PMCID for DOI 10.1371/journal.pone.0062199 of type <type 'str'>.
    """
    if not type(doi) == unicode:
        raise TypeError, "Cannot get PMCID for DOI %s of type %s." % (doi, type(doi))
    url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=%s' % doi
    xml_file = _get_file_from_url(url)
    tree = ElementTree()
    tree.parse(xml_file)
    try:
        return int(tree.find('IdList/Id').text)
    except AttributeError:
        return None

def get_pmid_from_doi(doi):
    """
    Return PMID of a document that has the given DOI.

    The input value of this function must have type “unicode”.
    The return value of this function has the type of “int”.

    >>> get_pmid_from_doi(u'10.1371/journal.pone.0062199')
    23620812
    >>> get_pmid_from_doi(u'10.1371/journal.pone.0093036')
    24695492
    >>> get_pmid_from_doi(u'10.1371/journal.pone.0099936')
    24927280

    >>> get_pmid_from_doi('10.1371/journal.pone.0062199')
    Traceback (most recent call last):
      ...
    TypeError: Cannot get PMID for DOI 10.1371/journal.pone.0062199 of type <type 'str'>.
    """
    if not type(doi) == unicode:
        raise TypeError, "Cannot get PMID for DOI %s of type %s." % (doi, type(doi))
    url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=%s' % doi
    xml_file = _get_file_from_url(url)
    tree = ElementTree()
    tree.parse(xml_file)
    try:
        return int(tree.find('IdList/Id').text)
    except AttributeError:
        return None

def get_categories_from_pmid(pmid):
    """
    Return categories of a document that has the given PMID.

    >>> for category in get_categories_from_pmid(23620812):
    ...     print category
    ... 
    Behavior, Animal
    Calcium
    Drosophila melanogaster
    Embryo, Nonmammalian
    Feedback, Sensory
    Larva
    Locomotion
    Motor Neurons
    Muscle Contraction
    Nerve Net
    Sensation
    Sense Organs
    Time Factors
    """
    if not type(pmid) == int:
        raise TypeError, "Cannot get Categories for PMID %s of type %s." % (pmid, type(pmid))
    url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=xml' % pmid
    xml_file = _get_file_from_url(url)
    tree = ElementTree()
    tree.parse(xml_file)
    categories = []
    for heading in tree.iterfind('PubmedArticle/MedlineCitation/MeshHeadingList/MeshHeading'):
        htree = ElementTree(heading)
        descriptor_text = htree.find('DescriptorName').text
        if (htree.find('QualifierName') is not None) or \
            (' ' in descriptor_text and not ' and ' in descriptor_text):
            categories.append(descriptor_text)
    return categories


if __name__ == "__main__":
    """Start doctests."""
    import doctest
    doctest.testmod()
