#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import date
from os import listdir, path
from sys import stderr
from urllib2 import urlopen, urlparse
from xml.etree.cElementTree import dump, ElementTree
# the C implementation of ElementTree is 5 to 20 times faster than the Python one

from hashlib import md5

import tarfile
import logging

# According to <ftp://ftp.ncbi.nlm.nih.gov/README.ftp>, this should be
# 33554432 (32MiB) for best performance. Note that on slow connections,
# however, huge buffers size leads to notable interface lag.
BUFSIZE = 33554432
#BUFSIZE = 1024000  # (1024KB)

def download_metadata(target_directory):
    """
    Downloads files from PubMed FTP server into given directory,
    yielding download status. This function is invoked by oa-get.

    This function is a generator and should only be invoked as such.
    """
    # This function has no doctest, because the files are too big.
    urls = [
        'ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.A-B.tar.gz',
        'ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.C-H.tar.gz',
        'ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.I-N.tar.gz',
        'ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/articles.O-Z.tar.gz'
    ]

    for url in urls:
        remote_file = urlopen(url)
        total = int(remote_file.headers['content-length'])
        completed = 0

        url_path = urlparse.urlsplit(url).path
        local_filename = path.join(target_directory, \
            url_path.split('/')[-1])

        # if local file has same size as remote file, skip download
        try:
            if (path.getsize(local_filename) == total):
                continue
        except OSError:  # local file does not exist
            pass

        with open(local_filename,'wb') as local_file:
            while True:
                chunk = remote_file.read(BUFSIZE)
                if chunk != '':
                    local_file.write(chunk)
                    completed += len(chunk)
                    yield {
                        'url': url,
                        'completed': completed,
                        'total': total
                    }
                else:
                    break

def list_articles(target_directory, supplementary_materials=False, skip=[]):
    """
    Iterates over archive files in target_directory, yielding article
    information in a dictionary. This function is invoked by oa-cache.

    The function utilizes the tarfile module so it does not have to
    store several Gigabytes of XML on space-limited permanent storage.

    This function is a generator and should only be invoked as such.
    """
    # This method has no doctest because the needed files are too big.
    listing = listdir(target_directory)
    for filename in listing:
        with tarfile.open(path.join(target_directory, filename)) as archive:
            for item in archive:
                if item.name in skip:
                    continue
                if path.splitext(item.name)[1] == '.nxml':
                    content = archive.extractfile(item)
                    tree = ElementTree()
                    tree.parse(content)

                    result = {}
                    result['name'] = item.name
                    skip.append(item.name)  # guard against duplicate input
                    result['doi'] = _get_article_doi(tree)
                    result['article-contrib-authors'] = _get_article_contrib_authors(tree)
                    result['article-title'] = _get_article_title(tree)
                    result['article-abstract'] = _get_article_abstract(tree)
                    result['journal-title'] = _get_journal_title(tree)
                    result['article-year'], \
                        result['article-month'], \
                        result['article-day'] = _get_article_date(tree)
                    result['article-url'] = _get_article_url(tree)
                    result['article-license-url'], \
                        result['article-license-text'], \
                        result['article-copyright-statement'] = _get_article_licensing(tree)
                    result['article-copyright-holder'] = _get_article_copyright_holder(tree)
                    result['article-categories'] = _get_article_categories(tree)

                    if supplementary_materials:
                        result['supplementary-materials'] = _get_supplementary_materials(tree)
                    yield result

def _strip_whitespace(text):
    r"""
    Strips leading and trailing whitespace for multiple lines.

    >>> print _strip_whitespace('  abc  \n  def  \n  ghi  ')
    abc
    def
    ghi
    """
    text = '\n'.join(
        [line.strip() for line in text.splitlines()]
    )
    return text.strip('\n')

def _get_article_categories(tree):
    """
    Given an ElementTree, return (some) article categories.
    """
    # This function currently has no doctest because the XML file used
    # for the other tests does not contain any categories.
    categories = []
    article_categories = ElementTree(tree).find('.//*article-categories')
    for subject_group in article_categories.iter('subj-group'):
        try:
            if subject_group.attrib['subj-group-type'] == 'heading':
                continue
        except KeyError:  # no attribute “subj-group-type”
            pass
        for subject in subject_group.iter('subject'):
            if subject.text is None:
                continue
            if '/' in subject.text:
                category_text = subject.text.split('/')[-1]
            else:
                category_text = subject.text
            if ' ' in category_text and not 'and' in category_text and \
                category_text not in categories:
                categories.append(category_text)
    keywords = []
    article_keywords = ElementTree(tree).find('.//*kwd-group')
    if article_keywords != None:
        for keyword in article_keywords.iter('kwd'):
            if keyword.text is None:
                continue
            keywords.append(keyword.text)
    return categories+keywords

def _get_article_contrib_authors(tree):
    """
    Given an ElementTree, returns article authors in a format suitable for citation.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_contrib_authors(article_tree)
    'Behnke J, Buttle D, Stepek G, Lowe A, Duce I'
    """
    authors = []
    front = ElementTree(tree).find('front')
    for contrib in front.iter('contrib'):
        if contrib.attrib['contrib-type'] != 'author':
            continue
        contribTree = ElementTree(contrib)
        try:
            surname = contribTree.find('name/surname').text
        except AttributeError:  # author is not a natural person
            try:
                citation_name = contribTree.find('collab').text
                if citation_name is not None:
                    authors.append(citation_name)
                continue
            except AttributeError:  # name has no immediate text node
                continue

        try:
            given_names = contribTree.find('name/given-names').text
            citation_name = ' '.join([surname, given_names[0]])
        except AttributeError:  # no given names
            citation_name = surname
        except TypeError:  # also no given names
            citation_name = surname
        if citation_name is not None:
            authors.append(citation_name)

    return ', '.join(authors)

def _get_article_title(tree):
    """
    Given an ElementTree, returns article title.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_title(article_tree)
    'Developing novel anthelmintics from plant cysteine proteinases'
    """
    title = ElementTree(tree).find('front/article-meta/title-group/article-title')
    if title is None:
        title = ElementTree(tree).find('front/article-meta/article-categories/subj-group/subject')
    return ''.join(title.itertext())

def _get_article_abstract(tree):
    """
    Given an ElementTree, returns article abstract.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_abstract(article_tree)
    'Intestinal helminth infections of livestock and humans are predominantly controlled by treatment with three classes of synthetic drugs, but some livestock nematodes have now developed resistance to all three classes and there are signs that human hookworms are becoming less responsive to the two classes (benzimidazoles and the nicotinic acetylcholine agonists) that are licensed for treatment of humans. New anthelmintics are urgently needed, and whilst development of new synthetic drugs is ongoing, it is slow and there are no signs yet that novel compounds operating through different modes of action, will be available on the market in the current decade. The development of naturally-occurring compounds as medicines for human use and for treatment of animals is fraught with problems. In this paper we review the current status of cysteine proteinases from fruits and protective plant latices as novel anthelmintics, we consider some of the problems inherent in taking laboratory findings and those derived from folk-medicine to the market and we suggest that there is a wealth of new compounds still to be discovered that could be harvested to benefit humans and livestock.'
    """
    for abstract in ElementTree(tree).iterfind('.//*abstract'):
        if 'abstract-type' in abstract.attrib:  # toc or summary
            continue
        else:
            return _strip_whitespace(''.join(abstract.itertext()))
    return None

def _get_journal_title(tree):
    """
    Given an ElementTree, returns journal title.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_journal_title(article_tree)
    'Parasites & Vectors'
    """
    front = ElementTree(tree).find('front')
    for journal_meta in front.iter('journal-meta'):
        for journal_title in journal_meta.iter('journal-title'):
            title = journal_title.text
            # take only the part before the colon, strip whitespace
            title = title.split(':')[0].strip()
            title = title.replace('PLoS', 'PLOS').replace('PloS', 'PLOS')
            return title

def _get_article_date(tree):
    """
    Given an ElementTree, returns article date as tuple of integers in
    the format (year, month, day).

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_date(article_tree)
    (2008, None, None)
    """
    article_meta = tree.find('front/article-meta')
    for pub_date in article_meta.iter('pub-date'):
        year = int(pub_date.find('year').text)
        try:
            month = int(pub_date.find('month').text)
        except AttributeError:
            return year, None, None
        try:
            day = int(pub_date.find('day').text)
        except AttributeError:
            return year, month, None
        return year, month, day
    raise RuntimeError, 'No date information found.'

def _get_article_url(tree):
    """
    Given an ElementTree, returns article URL.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_url(article_tree)
    'http://dx.doi.org/10.1186/1756-3305-1-29'
    """
    doi = _get_article_doi(tree)
    if doi:
        return 'http://dx.doi.org/' + doi

license_url_equivalents = {
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License, ( http://creativecommons.org/licenses/by/3.0/ ) which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.': 'http://creativecommons.org/publicdomain/zero/1.0/',
    u'>This work is licensed under a Creative Commons Attribution NonCommercial 3.0 License (CC BY-NC 3.0). Licensee PAGEPress, Italy': None,
    u'Available freely online through the author-supported open access option.': None,
    u'Distributed under the Hogrefe OpenMind License [ http://dx.doi.org/10.1027/a000001]': 'http://dx.doi.org/10.1027/a000001',
    u'Freely available online through the American Journal of Tropical Medicine and Hygiene Open Access option.': None,
    u'License information: This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0',
    u'Open Access': None,
    u'Readers may use this article as long as the work is properly cited, the use is educational and not for profit, and the work is not altered. See http://creativecommons.org/licenses/by -nc-nd/3.0/ for details.': None,
    u'Readers may use this article as long as the work is properly cited, the use is educational and not for profit, and the work is not altered. See http://creativecommons.org/licenses/by-nc-nd/3.0/ for details.': None,
    u'Readers may use this article as long as the work is properly cited, the use is educational and not for profit,and the work is not altered. See http://creativecommons.org/licenses/by-nc-nd/3.0/ for details.': None,
    u'Readers may use this article aslong as long as the work is properly cited, the use is educational and not for profit, and the work is not altered. See http://creativecommons.org/licenses/by-nc-nd/3.0/ for details.': None,
    u'The authors have paid a fee to allow immediate free access to this article.': None,
    u'The online version of this article has been published under an open access model, users are entitle to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and the European Society for Medical Oncology are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org': None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org': None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org.': None,
    u'The online version of this article has been published under an open access model. users are entitle to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and the European Society for Medical Oncology are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org': None,
    u'The online version of this article is published within an Open Access environment subject to the conditions of the Creative Commons Attribution-NonCommercial-ShareAlike licence < http://creativecommons.org/licenses/by-nc-sa/2.5/>. The written permission of Cambridge University Press must be obtained for commercial re-use': None,
    u'The online version of this article is published within an Open Access environment subject to the conditions of the Creative Commons Attribution-NonCommercial-ShareAlike licence < http://creativecommons.org/licenses/by-nc-sa/2.5/>. The written permission of Cambridge University Press must be obtained for commercial re-use.': None,
    u'Thi is an open access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This article is an open-access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ ).': 'http://creativecommons.org/licenses/by/3.0/',
    u'This article is in the public domain.': 'http://creativecommons.org/licenses/publicdomain/',
    u'This article, manuscript, or document is copyrighted by the American Psychological Association (APA). For non-commercial, education and research purposes, users may access, download, copy, display, and redistribute this article or manuscript as well as adapt, translate, or data and text mine the content contained in this document. For any such use of this document, appropriate attribution or bibliographic citation must be given. Users should not delete any copyright notices or disclaimers. For more information or to obtain permission beyond that granted here, visit http://www.apa.org/about/copyright.html.': None,
    u'This document may be redistributed and reused, subject to certain conditions .': None,
    u'This document may be redistributed and reused, subject to www.the-aps.org/publications/journals/funding_addendum_policy.htm .': None,
    u'This is a free access article, distributed under terms ( http://www.nutrition.org/publications/guidelines-and-policies/license/ ) which permit unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is a free access article, distributed under terms that permit unrestricted noncommercial use, distribution, and reproduction in any medium, provided the original work is properly cited. http://www.nutrition.org/publications/guidelines-and-policies/license/ .': None,
    u"This is an Open Access article distributed under the terms and of the American Society of Tropical Medicine and Hygiene's Re-use License which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.": None,
    u"This is an Open Access article distributed under the terms of the American Society of Tropical Medicine and Hygiene's Re-use License which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.": None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License ( http://creativecommons.org/licenses/by/2.0 ), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License ( http://creativecommons.org/licenses/by/3.0 ), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License (<url>http://creativecommons.org/licenses/by/2.0</url>), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License (http://creativecommons.org/licenses/by/2.0), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0 ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/uk/ ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5 ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5/ ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5/uk/ ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/3.0 ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/3.0/ ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/3.0/us/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses?by-nc/2.5 ), which permits unrestricted non-commercial use distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial Share Alike License ( http://creativecommons.org/licenses/by-nc-sa/3.0 ), which permits unrestricted non-commercial use, distribution and reproduction in any medium provided that the original work is properly cited and all further distributions of the work or adaptation are subject to the same Creative Commons License terms': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial Share Alike License ( http://creativecommons.org/licenses/by-nc-sa/3.0 ), which permits unrestricted non-commercial use, distribution and reproduction in any medium provided that the original work is properly cited and all further distributions of the work or adaptation are subject to the same Creative Commons License terms.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution licence which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution-Noncommercial License ( http://creativecommons.org/licenses/by-nc/3.0/ ), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited. Information for commercial entities is available online ( http://www.chestpubs.org/site/misc/reprints.xhtml ).': None,
    u'This is an Open Access article which permits unrestricted noncommercial use, provided the original work is properly cited.': None,
    u'This is an Open Access article which permits unrestricted noncommercial use, provided the original work is properly cited. Clinical Ophthalmology 2011:5 101\xe2\x80\x93108': None,
    u'This is an Open Access article: verbatim copying and redistribution of this article are permitted in all media for any purpose': None,
    u'This is an open access article distributed under the Creative Commons Attribution License, in which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0',
    u'This is an open access article distributed under the Creative Commons Attribution License, which permits unrestricted use, distribution and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open access article distributed under the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open access article distributed under the Creative Commons attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open access article distributed under the terms of the Creative Commons Attribution License ( http://creativecommons.org/licenses/by/2.0 ), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an open access article distributed under the terms of the Creative Commons Attribution License ( http://www.creativecommons.org/licenses/by/2.0 ) which permits unrestricted use, distribution and reproduction provided the original work is properly cited.': 'http://www.creativecommons.org/licenses/by/2.0',
    u'This is an open access article distributed under the terms of the Creative Commons Attribution License (<url>http://creativecommons.org/licenses/by/2.0</url>), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an open access article distributed under the terms of the Creative Commons Attribution License (http://creativecommons.org/licenses/by/2.0), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an open access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open access article distributed under theCreative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open access article. Unrestricted non-commercial use is permitted provided the original work is properly cited.': None,
    u'This is an open access paper distributed under the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0',
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution Non-commercial License, which permits use, distribution, and reproduction in any medium, provided the original work is properly cited, the use is non commercial and is otherwise in compliance with the license. See: http://creativecommons.org/licenses/by-nc/2.0/ and http://creativecommons.org/licenses/by-nc/2.0/legalcode .': None,
    u'This research note is distributed under the Commons Attribution-Noncommercial 3.0 License.': None,
    u'This research note is distributed under the Creative Commons Attribution 3.0 License.': 'http://creativecommons.org/licenses/by/3.0',
    u'This work is licensed under a Creative Commons Attr0ibution 3.0 License (by-nc 3.0). Licensee PAGE Press, Italy': None,
    u'This work is licensed under a Creative Commons Attribution 3.0 License (by-nc 3.0) Licensee PAGEPress, Italy': None,
    u'This work is licensed under a Creative Commons Attribution 3.0 License (by-nc 3.0). Licensee PAGE Press, Italy': None,
    u'This work is licensed under a Creative Commons Attribution 3.0 License (by-nc 3.0). Licensee PAGEPress, Italy': None,
    u'This work is licensed under a Creative Commons Attribution NonCommercial 3.0 License (CC BY-NC 3.0). Licensee PAGEPress srl, Italy': None,
    u'This work is licensed under a Creative Commons Attribution NonCommercial 3.0 License (CC BY-NC 3.0). Licensee PAGEPress, Italy': None,
    u'This work is subject to copyright. All rights are reserved, whether the whole or part of the material is concerned, specifically the rights of translation, reprinting, reuse of illustrations, recitation, broadcasting, reproduction on microfilm or in any other way, and storage in data banks. Duplication of this publication or parts thereof is permitted only under the provisions of the German Copyright Law of September 9, 1965, in its current version, and permission for use must always be obtained from Springer-Verlag. Violations are liable for prosecution under the German Copyright Law.': None,
    u'This work is subject to copyright. All rights are reserved, whether the whole or part of the material is concerned, specifically the rights of translation, reprinting, reuse of illustrations, recitation, broadcasting, reproduction on microfilm or in any other way, and storage in data banks. Duplication of this publication or parts thereof is permitted only under the provisions of the German Copyright Law of September 9, in its current version, and permission for use must always be obtained from Springer-Verlag. Violations are liable for prosecution under the German Copyright Law.': None,
    u'Users may view, print, copy, download and text and data- mine the content in such documents, for the purposes of academic research, subject always to the full Conditions of use: http://www.nature.com/authors/editorial_policies/license.html#terms': None,
    u'creative commons': None,
    u'\xc2\xa7 The authors have paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\x96 The authors have paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\x96The authors have paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\xa0 The author has paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\xa0 The authors have paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\xa0The authors have paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\xa1 The authors have paid a fee to allow immediate free access to this article': None,
    u'\xe2\x80\xa1 The authors have paid a fee to allow immediate free access to this article.': None,
    u'\xe2\x80\xa1The authors have paid a fee to allow immediate free access to this article.': None,
    u"You are free to share–to copy, distribute and transmit the work, under the following conditions: Attribution :  You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial :  You may not use this work for commercial purposes. No derivative works :  You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode. Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this license impairs or restricts the author's moral rights.": None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited. This paper is available online free of all access charges (see http://jxb.oxfordjournals.org/open_access.html for further details)': None,
    u'Royal College of Psychiatrists, This paper accords with the Wellcome Trust Open Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/Wellcome%20Trust%20licence.pdf' : None,
    u'This is an open access article distributed under the Creative Commons Attribution License,which permits unrestricted use,distribution,and reproduction in any medium,provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This paper is an open-access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ ).': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access articlewhich permits unrestricted noncommercial use, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-commercial License ( http://creativecommons.org/licences/by-nc/2.0/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited. This paper is available online free of all access charges (see http://jxb.oxfordjournals.org/open_access.html for further details)': None,
    u'This is an open access article distributed under the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work are properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License (<url>http://creativecommons.org/licenses/by/2.0</url>), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited': 'http://creativecommons.org/licenses/by/2.0',
     'This work is licensed under a Creative Commons Attribution 3.0 License (by-nc 3.0).': None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oupjournals.org': None,
    u"Author's Choice - Final Version Full Access NIH Funded Research - Final Version Full Access Creative Commons Attribution Non-Commercial License applies to Author Choice Articles": None,
    u'The online version of this article has been published under an open access model. users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commerical purposes provided that: the original authorship is properly and fully attributed; the Journal and the Guarantors of Brain are attributed as the original place of publication with the correction citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org.': None,
    u"You are free to share - to copy, distribute and transmit the work, under the following conditions: Attribution: You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial: You may not use this work for commercial purposes. No derivative works: You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode . Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this license impairs or restricts the author's moral rights.": None,
    u'Open access articles can be viewed online without a subscription.': None,
    u'‡ The authors have paid a fee to allow immediate free access to this work.': None,
    u'Published under the CreativeCommons Attribution-NonCommercial-NoDerivs 3.0 License .': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/uk/ ) which permits unrestricted non-commercial use distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/. )': 'http://creativecommons.org/licenses/by/3.0/',
    u'This work is licensed under a Creative Commons Attribution 3.0 License (by-nc 3.0)': None,
    u"Author's Choice —Final version full access. NIH Funded Research - Final version full access. Creative Commons Attribution Non-Commercial License applies to Author Choice Articles": None,
    u'This is an open-access article, which permits unrestricted use, distribution, and reproduction in any medium, for non-commercial purposes, provided the original author and source are credited.': None,
    u'This article is an open-access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ )': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial No Derivatives License ( http://creativecommons.org/licenses/by-nc-nd/3.0/ ), which permits for noncommercial use, distribution, and reproduction in any medium, provided the original work is properly cited and is not altered in any way.': None,
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license http://creativecommons.org/licenses/by/3.0/ .': 'http://creativecommons.org/licenses/by/3.0/',
    u"You are free to share–to copy, distribute and transmit the work, under the following conditions: Attribution :  You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial :  You may not use this work for commercial purposes. No derivative works :  You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode . Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this license impairs or restricts the author's moral rights.": None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/y-nc/2.0/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This work is licensed under a Creative Commons Attribution Noncommercial 3.0 License (CC BYNC 3.0). Licensee PAGEPress, Italy': None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org Published by Oxford University Press on behalf of the International Epidemiological Association': None,
    u'This is an open access article distributed under the Creative Commons Attribution License which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u"You are free to share - to copy, distribute and transmit the work, under the following conditions: Attribution:   You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial:   You may not use this work for commercial purposes. No derivative works:   You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode . Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this license impairs or restricts the author's moral rights.": None,
    u'This article is distributed under the terms of an Attribution–Noncommercial–Share Alike–No Mirror Sites license for the first six months after the publication date (see http://www.jem.org/misc/terms.shtml ). After six months it is available under a Creative Commons License (Attribution–Noncommercial–Share Alike 3.0 Unported license, as described at http://creativecommons.org/licenses/by-nc-sa/3.0/ ).': None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for noncommercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/byc/2.5 ), which permits unrestricted nonommercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press and The Japanese Society for Immunology are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org': None,
    u'# The authors have paid a fee to allow immediate free access to this paper.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License (http://creativecommons.org/licenses/by-nc/2.0/uk/) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This work is licensed under a Creative Commons Attribution NonCommercial 3.0 License (CC BYNC 3.0). LicenseePAGEPress, Italy': None,
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ ).': 'http://creativecommons.org/licenses/by/3.0/',
    u"Author's Choice - Final Version Full Access Creative Commons Attribution Non-Commercial License applies to Author Choice Articles": None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited. This paper is available online free of all access charges (see http://jxb.oxfordjournals.org/open_access.html for further details)': None,
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ )': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open access article distributed under the Creative Commons Attribution License, that permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ .)': 'http://creativecommons.org/licenses/by/3.0/',
    u"Author's Choice —Final version full access. Creative Commons Attribution Non-Commercial License applies to Author Choice Articles": None,
    u'¶ The authors have paid a fee to allow immediate free access to this article.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5 ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited. This paper is available online free of all access charges (see http://jxb.oxfordjournals.org/open_access.html for further details)': None,
    u'This article is distributed under the terms of an Attribution–Noncommercial–Share Alike–No Mirror Sites license for the first six months after the publication date (see http://www.jcb.org/misc/terms.shtml ). After six months it is available under a Creative Commons License (Attribution–Noncommercial–Share Alike 3.0 Unported license, as described at http://creativecommons.org/licenses/by-nc-sa/3.0/ ).': None,
    u'99This is an open access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u"You are free to share–to copy, distribute and transmit the work, under the following conditions: Attribution :  You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial :  You may not use this work for commercial purposes. No derivative works :  You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode. Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this lincense impairs or restricts the author's moral rights.": None,
    u'This is an open access article distributed under the terms of the creative commons attribution license, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'Royal College of Psychiatrists, This paper accords with the NIH Public Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/NIH%20licence%20agreement.pdf Royal College of Psychiatrists, This paper accords with the Wellcome Trust Open Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/Wellcome%20Trust%20licence.pdf': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/uk/> ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This article is an Open Access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/ ).': 'http://creativecommons.org/licenses/by/3.0/',
    u'Available online without subscription through the open access option.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This article is distributed under the terms of an Attribution–Noncommercial–Share Alike–No Mirror Sites license for the first six months after the publication date (see http://www.jgp.org/misc/terms.shtml ). After six months it is available under a Creative Commons License (Attribution–Noncommercial–Share Alike 3.0 Unported license, as described at http://creativecommons.org/licenses/by-nc-sa/3.0/ ).': None,
    u'This is an open access article distributed under the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original paper is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License ( http://creativecommons.org/licenses/by/3.0/ ), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license ( http://creativecommons.org/licenses/by/3.0/': 'http://creativecommons.org/licenses/by/3.0/',
    u"You are free to share - to copy, distribute and transmit the work, under the following conditions: Attribution:   You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial:   You may not use this work for commercial purposes. No derivative works:   You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode. Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this license impairs or restricts the author's moral rights.": None,
    u"This is an Open Access article: verbatim copying and redistribution of this article are permitted in all media for any purpose, provided this notice is preserved along with the article's original URL.": None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5 ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This article is an open-access article distributed under the terms and conditions of the Creative Commons Attribution license http://creativecommons.org/licenses/by/3.0/ .': 'http://creativecommons.org/licenses/by/3.0/',
    u'Published under the CreativeCommons Attribution NonCommercial-NoDerivs 3.0 License .': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/3.0 ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited. This paper is available online free of all access charges (see http://jxb.oxfordjournals.org/open_access.html for further details)': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-ommercial License ( http://creativecommons.org/licenses/byc/2.5 ), which permits unrestricted nonommercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This paper accords with the Wellcome Trust Open Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/Wellcome%20Trust%20licence.pdf': None,
    u'This paper accords with the NIH Public Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/NIH%20licence%20agreement.pdf This paper accords with the Wellcome Trust Open Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/Wellcome%20Trust%20licence.pdf': None,
    u'This article is an Open Access article distributed under the terms and conditions of the Creative Commons Attribution license http://creativecommons.org/licenses/by/3.0/ .': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses?by-nc/2.0/uk/ ) which permits unrestricted non-commercial use distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons-Attribution Noncommercial License ( http://creativecommons.org/licenses/by-nc/2.0/ ), which permits unrestricted noncommercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'Creative Commons Attribution Non-Commercial License applies to Author Choice Articles': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5 ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited. This paper is available online free of all access charges (see http://jxb.oxfordjournals.org/open_access.html for further details)': None,
    u'This is an open access article distributed under the terms of the creative commons attribution license, which permits unrestricteduse, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'available online without subscription through the open access option.': None,
    u"Author's Choice": None,
    u'# The authors have paid a fee to allow immediate free access to this article.': None,
    u'Open Access articles can be viewed online without a subscription.': None,
    u'This is an open access article distributed under the terms of the Creative Commons Attribution License (<url>http://creativecommons.org/licenses/by/2.0</url>), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited': 'http://creativecommons.org/licenses/by/2.0',
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u"Author's Choice —Final version full access.": None,
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution-Noncommercial-Share Alike 3.0 Unported License, which permits unrestricted noncommercial use, distribution, and reproduction in any medium, provided the original author and source are credited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution License ( http://creativecommons.org/licenses/by/2.0 ), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited': 'http://creativecommons.org/licenses/by/2.0',
    u"Author's Choice - Final version full access. Creative Commons Attribution Non-Commercial License applies to Author Choice Articles": None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and Oxford University Press are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org Published by Oxford University Press on behalf of the International Epidemiological Association.': None,
    u"You are free to share - to copy, distribute and transmit the work, under the following conditions: Attribution :  You must attribute the work in the manner specified by the author or licensor (but not in any way that suggests that they endorse you or your use of the work). Non-commercial :  You may not use this work for commercial purposes. No derivative works :  You may not alter, transform, or build upon this work. For any reuse or distribution, you must make clear to others the license terms of this work, which can be found at http://creativecommons.org/licenses/by-nc-nd/3.0/legalcode . Any of the above conditions can be waived if you get permission from the copyright holder. Nothing in this license impairs or restricts the author's moral rights.": None,
    u'The Author(s) This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.0/uk/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution-Noncommercial License ( http://creativecommons.org/licenses/by-nc/3.0/ ), which permits unrestricted use, distribution, and reproduction in any noncommercial medium, provided the original work is properly cited.': None,
    u"Author's Choice Creative Commons Attribution Non-Commercial License applies to Author Choice Articles": None,
    u'The online version of this article has been published under an open access model. Users are entitled to use, reproduce, disseminate, or display the open access version of this article for non-commercial purposes provided that: the original authorship is properly and fully attributed; the Journal and the Japanese Society of Plant Physiologists are attributed as the original place of publication with the correct citation details given; if an article is subsequently reproduced or disseminated not in its entirety but only in part or as a derivative work this must be clearly indicated. For commercial re-use, please contact journals.permissions@oxfordjournals.org': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial No Derivatives License, which permits for noncommercial use, distribution, and reproduction in any digital medium, provided the original work is properly cited and is not altered in any way.': None,
    u'This paper accords with the NIH Public Access policy and is governed by the licence available at http://www.rcpsych.ac.uk/pdf/NIH%20licence%20agreement.pdf': None,
    u'This work is licensed under a Creative Commons Attribution NonCommercial 3.0 License (CC BYNC 3.0). Licensee PAGEPress, Italy': None,
    u'This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution license http://creativecommons.org/licenses/by/3.0/.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License ( http://creativecommons.org/licenses/by-nc/2.5 ), which permits unrestricted non-commercial use, distribution and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial License http://creativecommons.org/licenses/by-nc/2.5/ ) which permits unrestricted non-commercial use, distribution, and reproduction in any medium, provided the original work is properly cited.': None,
    u'This is an open access article distributed under the Creative Commons Attribution License , which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an Open Access article distributed under the terms of the Creative Commons Attribution Non-Commercial No Derivatives License, which permits for noncommercial use, distribution, and reproduction in any digital medium, provided the original work is properly cited and is not altered in any way. For details, please refer to http://creativecommons.org/licenses/by-nc-nd/3.0/': None,
    u'This document may be redistributed and reused, subject to certain conditions .': None,
    u'Re-use of this article is permitted in accordance with the Creative Commons Deed, Attribution 2.5, which does not permit commercial exploitation.': None,
    u'This article is published under license to BioMed Central Ltd. This is an Open Access article distributed under the terms of the Creative Commons Attribution License (<ext-link ext-link-type="uri" xlink:href="http://creativecommons.org/licenses/by/2.0">http://creativecommons.org/licenses/by/2.0</ext-link>), which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.': 'http://creativecommons.org/licenses/by/2.0'
}

copyright_statement_url_equivalents = {
    u'Chiropractic & Osteopathic College of Australasia': None,
    u'Copyright © 2008 by S. Karger AG, Basel': None,
    u'Copyright © 2009 by S. Karger AG, Basel': None,
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited': 'http://creativecommons.org/licenses/by/3.0/',
    u'This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.': 'http://creativecommons.org/publicdomain/zero/1.0/',
    u'This is an open-access article distributed under the terms of the Creative Commons Public Domain declaration which stipulates that, once placed in the public domain, this work may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose.': 'http://creativecommons.org/publicdomain/zero/1.0/',
    u'This is an open-access article distributed under the terms of the Creative Commons Public Domain declaration, which stipulates that, once placed in the public domain, this work may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose.': 'http://creativecommons.org/publicdomain/zero/1.0/',
    u"This is an Open Access article: verbatim copying and redistribution of this article are permitted in all media for any purpose, provided this notice is preserved along with the article's original URL.": None,
    u'© Biomedical Engineering Society 2010': None,
    u'© Springer Science+Business Media, Inc. 2007': None,
    u'© Springer Science+Business Media, LLC 2007': None,
    u'© Springer Science+Business Media, LLC 2008': None,
    u'© Springer Science+Business Media, LLC 2009': None,
    u'© Springer Science+Business Media, LLC 2010': None,
    u'© Springer Science+Business Media, LLC 2011': None,
    u'© Springer Science+Business Media, LLC and the Cardiovascular and Interventional Radiological Society of Europe (CIRSE) 2009': None,
    u'© Springer Science+Business Media, LLC and the Cardiovascular and Interventional Radiological Society of Europe (CIRSE) 2010': None,
    u'© Springer Science+Business Media B.V. 2006': None,
    u'© Springer Science+Business media B.V. 2006': None,
    u'© Springer Science+Business Media B.V. 2007': None,
    u'© Springer Science + Business Media B.V. 2007': None,
    u'© Springer Science+Business Media B.V. 2008': None,
    u'© Springer Science+Business Media B.V. 2009': None,
    u'© Springer Science+Business Media B.V. 2010': None,
    u'© Springer Science+Business Media B.V. 2011': None,
    u'© Springer-Verlag 2007': None,
    u'© Springer-Verlag 2008': None,
    u'© Springer-Verlag 2009': None,
    u'© Springer-Verlag 2010': None,
    u'Copyright © 2011 Macmillan Publishers Limited': None,
    u'Copyright © 2012 Macmillan Publishers Limited': None,
    u'© 2007 The Authors Journal compilation © 2007 Blackwell Publishing Ltd': None,
    u'© 2008 Dove Medical Press Limited. All rights reserved': None,
    u'© The Author(s) 2007': None,
    u'© The Author(s) 2008': None,
    u'© The Author(s) 2009': None,
    u'© The Author(s) 2010': None,
    u'© The Author(s) 2011': None,
    u'© The Author(s) 2012': None,
}

license_url_fixes = {
    'http://creativecommons.org/Licenses/by/2.0': 'http://creativecommons.org/licenses/by/2.0/',
    '(http://creativecommons.org/licenses/by/2.0)': 'http://creativecommons.org/licenses/by/2.0/',
    'http://(http://creativecommons.org/licenses/by/2.0)': 'http://creativecommons.org/licenses/by/2.0/',
    'http://creativecommons.org/licenses/by/2.0': 'http://creativecommons.org/licenses/by/2.0/',
    'http://creativecommons.org/licenses/by/3.0': 'http://creativecommons.org/licenses/by/3.0/',
    'http://creativecommons.org/licenses/by/4.0': 'http://creativecommons.org/licenses/by/4.0/',
    'http://creativecommons.org/licenses/by/4.0/legalcode': 'http://creativecommons.org/licenses/by/4.0/'
}


def _get_article_license_url(tree):
    """
    Given an ElementTree, return license URL.

    The license URL can be found URL in the xlink:href attribute of a
    <license> element:

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_license_url(article_tree)
    'http://creativecommons.org/licenses/by/2.0'

    The license URL can be found in the xlink:href attribute of a
    <ext-link> element that is a child of a <license-p> element:

    >>> with open('tests/10.1371/journal.pone.0087644.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_license_url(article_tree)
    'http://creativecommons.org/licenses/by/4.0/'
    """
    url = None
    license = tree.find('front//*license')
    if license is not None:
        try:
            url = license.attrib['{http://www.w3.org/1999/xlink}href']
        except KeyError:
            try:
                ext_link = license.find('license-p/ext-link')
                if ext_link is not None:
                    url = ext_link.attrib['{http://www.w3.org/1999/xlink}href']
            except KeyError:
                pass
    return url


def _get_article_license_text(tree):
    """
    Given an ElementTree, return license text.

    >>> with open('tests/10.1371/journal.pone.0062199.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_license_text(article_tree)
    u'This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.'
    """
    text = None
    license = tree.find('front//*license')
    if license is not None:
        text = u' '.join(license.itertext()).strip()
    return text


def _get_article_copyright_statement(tree):
    """
    Given an ElementTree, return copyright statement text.
    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_copyright_statement(article_tree)
    u'Copyright \\xa9 2008 Behnke et al; licensee BioMed Central Ltd.'
    """
    text = None
    copyright_statement = tree.find('front//*copyright-statement')
    if copyright_statement is not None:
        text = u' '.join(copyright_statement.itertext()).strip()
    return text


def _guess_license_url_from_license_url(url):
    """
    Return license URL for a given license URL.

    This function is intended to fix typos.

    >>> url = 'http://(http://creativecommons.org/licenses/by/2.0)'
    >>> _guess_license_url_from_license_url(url)
    'http://creativecommons.org/licenses/by/2.0/'
    """
    if url in license_url_fixes.keys():
        url = license_url_fixes[url]
    return url


def _guess_license_url_from_license_text(text):
    """
    Return license URL for a given license text.

    >>> text = u'License information: This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.'
    >>> _guess_license_url_from_license_text(text)
    'http://creativecommons.org/licenses/by/3.0'
    """
    url = None
    if text is not None:
        try:
            url = license_url_equivalents[text]
        except KeyError:
            logging.warning('Unknown license: %s', text)
    return url


def _guess_license_url_from_copyright_statement(text):
    """
    Return license URL for a given copyright statement.

    >>> text = u'This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.'
    >>> _guess_license_url_from_copyright_statement(text)
    'http://creativecommons.org/publicdomain/zero/1.0/'
    """
    url = None
    if text is not None:
        for key_text in copyright_statement_url_equivalents.keys():
            if text.endswith(key_text):
                url = copyright_statement_url_equivalents[key_text]
        if url is None:
            logging.warning('Unknown copyright statement :%s', text)
    return url


def _get_article_licensing(tree):
    """
    Given an ElementTree, return tuple consisting of article license
    URL, article license text, article copyright statement text.

    >>> with open('tests/10.1371/journal.pcbi.1003447.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_licensing(article_tree)
    ('http://creativecommons.org/publicdomain/zero/1.0/', u'This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.', None)
    """
    license_text = _get_article_license_text(tree)
    license_url = _get_article_license_url(tree)
    copyright_statement = _get_article_copyright_statement(tree)

    if license_url is not None:
        license_url = _guess_license_url_from_license_url(license_url)

    if license_url is None:
        license_url = _guess_license_url_from_license_text(license_text)

    if license_url is None:
        license_url = \
            _guess_license_url_from_copyright_statement(copyright_statement)

    return license_url, license_text, copyright_statement


def _get_article_copyright_holder(tree):
    """
    Given an ElementTree, returns article copyright holder.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_copyright_holder(article_tree)
    'Behnke et al; licensee BioMed Central Ltd.'
    """
    copyright_holder = tree.find(
        'front/article-meta/permissions/copyright-holder'
    )
    try:
        copyright_holder = copyright_holder.text
        if copyright_holder is not None:
            return copyright_holder
    except AttributeError:  # no copyright_holder known
        pass

    copyright_statement = tree.find('.//*copyright-statement')
    try:
        copyright_statement = copyright_statement.text
        if copyright_statement is not None:
            return copyright_statement.split('.')[0] + '.'
    except AttributeError:
        pass

    return None

def _get_supplementary_materials(tree):
    """
    Given an ElementTree, returns a list of article supplementary materials.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         materials = _get_supplementary_materials(article_tree)

    The materials list contains dictionaries for each supplementary material:

    >>> materials[0]['mimetype']
    'video'
    >>> materials[0]['title']
    'Additional file 1'
    >>> materials[0]['url']
    'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2559997/bin/1756-3305-1-29-S1.mpg'
    >>> materials[0]['mime-subtype']
    'mpeg'
    >>> materials[0]['label']
    ''
    >>> materials[0]['caption'][0:22] + u'...'
    u'A single adult female ...'

    """
    materials = []
    for sup in tree.iter('supplementary-material'):
        material = _get_supplementary_material(tree, sup)
        if material is not None:
            materials.append(material)
    for fig in tree.iter('fig'):
        material = _get_supplementary_material(tree, fig)
        if material is not None:
            materials.append(material)
    return materials

def _get_supplementary_material(tree, sup):
    """
    Given an ElementTree returns supplementary materials as a
    dictionary containing url, mimetype and label and caption.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         for sup in article_tree.iter('supplementary-material'):
    ...            material = _get_supplementary_material(article_tree, sup)

    >>> material['mimetype']
    'video'
    >>> material['title']
    'Additional file 1'
    >>> material['url']
    'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2559997/bin/1756-3305-1-29-S1.mpg'
    >>> material['mime-subtype']
    'mpeg'
    >>> material['label']
    ''
    >>> material['caption'][0:22] + u'...'
    u'A single adult female ...'
    """
    result = {}
    sup_tree = ElementTree(sup)

    label = sup_tree.find('label')
    result['label'] = ''
    if label is not None:
        result['label'] = label.text

    title = sup_tree.find('caption/title')
    result['title'] = ''
    if title is not None:
        title = _strip_whitespace(' '.join(title.itertext()))
        result['title'] = title

    caption = sup_tree.find('caption')
    result['caption'] = ''
    if caption is not None:
        caption_without_title = []
        for node in caption:
            if node.tag != 'title':
                caption_without_title.append(''.join(node.itertext()))
        caption = _strip_whitespace('\n'.join(caption_without_title))
        # remove file size and type information, e.g. “(1.3 MB MPG)”
        lastline = caption.split('\n')[-1]
        if lastline.startswith('(') and lastline.endswith(')'):
            caption = ' '.join(caption.split('\n')[:-1])
        assert 'Click here' not in caption
        result['caption'] = caption

    media = sup_tree.find('media')
    if media is not None:
        try:
            result['mimetype'] = media.attrib['mimetype']
            result['mime-subtype'] = media.attrib['mime-subtype']
        except KeyError:
            result['mimetype'] = ''
            result['mime-subtype'] = ''
        result['url'] = _get_supplementary_material_url(
            _get_pmcid(tree),
            media.attrib['{http://www.w3.org/1999/xlink}href']
        )
        return result

def _get_pmcid(tree):
    """
    Given an ElementTree, returns PubMed Central ID of article.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_pmcid(article_tree)
    '2559997'
    """
    front = ElementTree(tree).find('front')
    for article_id in front.iter('article-id'):
        if article_id.attrib['pub-id-type'] == 'pmc':
            return article_id.text

def _get_article_doi(tree):
    """
    Given an ElementTree, returns DOI for article.

    >>> with open('tests/10.1186/1756-3305-1-29.xml') as content:
    ...     tree = ElementTree().parse(content)
    ...     for article_tree in tree.iterfind('article'):
    ...         _get_article_doi(article_tree)
    '10.1186/1756-3305-1-29'

    """
    front = ElementTree(tree).find('front')
    for article_id in front.iter('article-id'):
        try:
            if article_id.attrib['pub-id-type'] == 'doi':
                return article_id.text
        except KeyError:
            pass

def _get_supplementary_material_url(pmcid, href):
    """
    This function creates absolute URIs for supplementary materials,
    using a PubMed Central ID and a relative URI.
    """
    return str('http://www.ncbi.nlm.nih.gov/pmc/articles/PMC' + pmcid +
        '/bin/' + href)


if __name__ == "__main__":
    """Start doctests."""
    import doctest
    doctest.testmod()
