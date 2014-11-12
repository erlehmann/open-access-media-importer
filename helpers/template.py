#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


def _escape(text):
    """
    Return given text escaped for MediaWiki markup.

    >>> _escape('abc = 123')
    'abc {{=}} 123'
    >>> _escape('def | ghi')
    'def {{!}} ghi'
    """
    for original, replacement in [
        ('=', '{{=}}'),
        ('|', '{{!}}')
    ]:
        try:
            text = text.replace(original, replacement)
        except AttributeError:
            pass
    return text


def _trim(text):
    """
    Return given text with spaces collapsed to one space and trimmed.

    >>> _trim('  The  quick  brown  fox  jumps  over  the  lazy  dog.  ')
    'The quick brown fox jumps over the lazy dog.'
    """
    return ' '.join(text.split())


def _capitalize_properly(word):
    """
    Return given text lowercased if all letters after first are lower cased.

    Single letters pass through unchanged.

    >>> [_capitalize_properly(w) for w in 'A', 'Ape', 'DNA', 'HeLa']
    ['A', 'ape', 'DNA', 'HeLa']

    """
    if len(word) == 1:
        return word
    if word[1:] == word[1:].lower():  # word has no capital letters inside
        return word.lower()
    else:  # words like 'DNA' or 'HeLa' should not be touched
        return word


def _postprocess_category(category):
    """
    Return text, slightly adjusted.

    This function removes category suffixes in parentheses from the
    result. It also prepends category suffixes that occur after a
    comma. It selectively lower cases and captitalizes the result.

    >>> _postprocess_category('blurb (blarb)')
    'Blurb'

    Selective lower casing is done by splitting category names along
    spaces and dashes and and using _capitalize_properly on the parts.

    >>> _postprocess_category('Protein Kinases, Cyclic AMP-Dependent')
    'Cyclic AMP-dependent protein kinases'

    """
    if '(' in category:
        category = category.split('(')[0]
    if ',' in category:
        category_parts = category.split(',')
        category_parts.reverse()
        category = ' '.join(category_parts)
    processed_category = []
    for word in category.strip().split(' '):
        wordparts = []
        for part in word.split('-'):
            wordparts.append(_capitalize_properly(part))
        processed_category.append('-'.join(wordparts))
    category = ' '.join(processed_category)
    return category[0].capitalize() + category[1:]


def get_license_template(url):
    """
    Return MediaWiki template markup for given license URL.

    >>> get_license_template('http://creativecommons.org/licenses/by-sa/4.0/')
    '{{cc-by-sa-4.0}}'
    """
    license_templates = {
        u'http://creativecommons.org/licenses/by/2.0/': '{{cc-by-2.0}}',
        u'http://creativecommons.org/licenses/by-sa/2.0/': '{{cc-by-sa-2.0}}',
        u'http://creativecommons.org/licenses/by/2.5/': '{{cc-by-2.5}}',
        u'http://creativecommons.org/licenses/by-sa/2.5/': '{{cc-by-sa-2.5}}',
        u'http://creativecommons.org/licenses/by/3.0/': '{{cc-by-3.0}}',
        u'http://creativecommons.org/licenses/by-sa/3.0/': '{{cc-by-sa-3.0}}',
        u'http://creativecommons.org/licenses/by/4.0/': '{{cc-by-4.0}}',
        u'http://creativecommons.org/licenses/by-sa/4.0/': '{{cc-by-sa-4.0}}'
    }
    return license_templates[url]


def make_description(title, caption):
    """
    Returns description merged from title and caption.

    >>> make_description('foo', 'bar')
    'foo bar'

    This function ignores filler title text like “Additional file 1”.

    >>> make_description('Additional file 1', 'baz')
    'baz'
    """
    if (title == 'Supplementary Data') or \
        (title == 'Supplementary Data') or \
        (title == 'Supplementary material') or \
        (title.startswith('Additional file') and len(title.split()) == 3):
        description = _escape(caption)  # title useless, not using it
    else:
        description = "%s %s" % (_escape(title), _escape(caption))
    return description


def make_wiki_filename(material_url, mimetype, article_title):
    """
    Return a file name for a supplementary material suitable for use
    in MediaWiki.

    The file name is constructed from the supplementary material's
    URL, its media type and the title of the article to which the
    supplementary material belongs.

    >>> make_wiki_filename('http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4210201/bin/pone.0110628.s008.mp4', 'video', 'Looking the Cow in the Eye: Deletion in the NID1 Gene Is Associated with Recessive Inherited Cataract in Romagnola Cattle')
    u'Looking-the-Cow-in-the-Eye-Deletion-in-the-NID1-Gene-Is-Associated-with-Recessive-Inherited-pone.0110628.s008.ogv'
    """
    url_path = urlparse.urlsplit(material_url).path
    source_filename = url_path.split('/')[-1]
    assert(mimetype in ('audio', 'video'))
    if mimetype == 'audio':
        extension = 'oga'
    elif mimetype == 'video':
        extension = 'ogv'
    wiki_filename = path.splitext(source_filename)[0] + '.' + extension
    if article_title is not None:
        dirty_prefix = article_title
        dirty_prefix = dirty_prefix.replace('\n', '')
        dirty_prefix = ' '.join(dirty_prefix.split()) # remove multiple spaces
        forbidden_chars = u"""?,;:^/!<>"`'±#[]|{}ʻʾʿ᾿῾‘’“”"""
        for character in forbidden_chars:
            dirty_prefix = dirty_prefix.replace(character, '')
        # prefix is first hundred chars of title sans forbidden characters
        prefix = '-'.join(dirty_prefix[:100].split(' '))
        # if original title is longer than cleaned up title, remove last word
        if len(dirty_prefix) > len(prefix):
            prefix = '-'.join(prefix.split('-')[:-1])
        if prefix[-1] != '-':
           prefix += '-'
        wiki_filename = prefix + wiki_filename
    return wiki_filename


def make_wiki_page(article_doi, article_pmid, article_pmcid, authors, article_title, journal_title, \
    article_year, article_month, article_day, article_url, license_url, label, caption, \
    title, categories, mimetype, material_url):
    """Return MediaWiki markup of page for given supplementary material."""
    license_template = get_license_template(license_url)

    text = "=={{int:filedesc}}==\n\n"
    text += "{{Information\n"

    description = make_description(title, caption)
    text += "|Description=\n"
    if len(description.strip()) > 0:
        text+= "{{en|1=%s}}\n" % description
    text += "|Date= %s\n" % make_datestring(article_year, article_month, article_day)
    if not label:
        label = ("%s file" % mimetype).capitalize()
    text += "|Source= [%s %s] from " % (material_url, _escape(label))
    text += "{{Cite journal\n"
    text += "| author = %s\n" % _escape(authors)
    text += "| title = %s\n" % _escape(_trim(article_title))
    text += "| doi = %s\n" % _escape(article_doi)
    text += "| journal = %s\n" % _escape(journal_title)
    text += "| year = %s\n" % _escape(article_year)
    pmid = article_pmid
    if pmid:
        text += "| pmid = %s\n" % _escape(pmid)
    pmcid = article_pmcid
    if pmcid:
        text += "| pmc = %s\n" % _escape(pmcid)
    text += "}}\n"
    text += "|Author= %s\n" % _escape(authors)
    text += "|Permission= %s\n" % license_template
    text += "|Other_fields={{Information field|name=Provenance|value= {{Open Access Media Importer}} }}\n"
    text += "}}\n\n"

    for category in categories:
        category = _postprocess_category(category)
        if len(category.split()) > 1:  # no single-word categories
            text += "[[Category:%s]]\n" % _escape(category)
    text += "[[Category:Media from %s]]\n" % _escape(journal_title)
    text += "[[Category:Uploaded with Open Access Media Importer]]\n"
    text += '[[Category:Uploaded with Open Access Media Importer and needing category review]]\n'
    if mimetype == 'audio':
        text += '[[Category:Audio files from open-access scholarly articles]]'
    if mimetype == 'video':
        text += '[[Category:Videos from open-access scholarly articles]]'
    return text


if __name__ == "__main__":
    """Start doctests."""
    import doctest
    doctest.testmod()
