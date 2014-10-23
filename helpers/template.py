#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import make_datestring

def _escape(text):
    """Return given text escaped for MediaWiki markup."""
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
    """Return given text without superfluous whitespace."""
    return ' '.join(text.split())

def _capitalize_properly(word):
    """
    Return given text lowercased if all letters after the first are already lower cased.
    """
    if len(word) == 1: # single letters should pass through unchanged
        return word
    if word[1:] == word[1:].lower():  # word has no capital letters inside
        return word.lower()
    else:  # words like 'DNA' or 'HeLa' should not be touched
        return word

def _postprocess_category(category):
    """Return category, slightly adjusted."""
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
    """Return MediaWiki template markup for given license URL."""
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
    """Returns description merged from suitable title and caption."""
    if (title == 'Supplementary Data') or \
        (title == 'Supplementary Data') or \
        (title == 'Supplementary material') or \
        (title.startswith('Additional file') and len(title.split()) == 3):
        description = _escape(caption)  # title useless, not using it
    else:
        description = "%s %s" % (_escape(title), _escape(caption))
    return description

def page(article_doi, article_pmid, article_pmcid, authors, article_title, journal_title, \
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
