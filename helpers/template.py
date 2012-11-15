#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import make_datestring

def _escape(text):
    for original, replacement in [
        ('=', '{{=}}'),
        ('|', '{{!}}')
    ]:
        try:
            text = text.replace(original, replacement)
        except AttributeError:
            pass
    return text

def page(article_doi, article_pmid, article_pmcid, authors, article_title, journal_title, \
    article_year, article_month, article_day, article_url, license_url, label, caption, \
    title, categories):
    license_templates = {
        u'http://creativecommons.org/licenses/by/2.0/': '{{cc-by-2.0}}',
        u'http://creativecommons.org/licenses/by-sa/2.0/': '{{cc-by-sa-2.0}}',
        u'http://creativecommons.org/licenses/by/2.5/': '{{cc-by-2.5}}',
        u'http://creativecommons.org/licenses/by-sa/2.5/': '{{cc-by-sa-2.5}}',
        u'http://creativecommons.org/licenses/by/3.0/': '{{cc-by-3.0}}',
        u'http://creativecommons.org/licenses/by-sa/3.0/': '{{cc-by-sa-3.0}}'
    }
    if 'PLOS' in journal_title:
        license_template = '{{PLOS}}'
    else:
        license_template = license_templates[license_url]

    text = "=={{int:filedesc}}==\n\n"
    text += "{{Information\n"
    if (title == 'Supplementary Data') or \
        (title == 'Supplementary Data') or \
        (title == 'Supplementary material') or \
        (title.startswith('Additional file') and len(title.split()) == 3):
        description = _escape(caption)  # title useless, not using it
    else:
        description = "%s %s" % (_escape(title), _escape(caption))
    text += "|Description=\n{{en|1=%s}}\n" % description
    text += "|Date= %s\n" % make_datestring(article_year, article_month, article_day)
    if label:
        text += "|Source= %s from " % _escape(label)
    else:
        text += "|Source= "
    text += "{{Cite journal\n"
    text += "| author = %s\n" % _escape(authors)
    text += "| title = %s\n" % _escape(article_title)
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

    def _postprocess_category(category):
        if '(' in category:
            category = category.split('(')[0]
        if ',' in category:
            category_parts = category.split(',')
            category_parts.reverse()
            category = ' '.join(category_parts)
        processed_category = []
        for i, word in enumerate(category.strip().split()):
            if word[1:] == word[1:].lower():
            # lower only words that do no have capital letters inside
                word = word.lower()
                if i == 0:  # capitalize first word
                    word = word.capitalize()
            processed_category.append(word)
        return ' '.join(processed_category)

    for category in categories:
        text += "[[Category:%s]]\n" % _escape(_postprocess_category(category))
    text += "[[Category:Media from %s]]\n" % _escape(journal_title)
    text += "[[Category:Uploaded with Open Access Media Importer]]\n"
    text += '[[Category:Uploaded with Open Access Media Importer and needing category review]]\n'
    return text
