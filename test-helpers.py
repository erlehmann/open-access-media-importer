#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from helpers import make_datestring, filename_from_url, efetch, mediawiki, template
from helpers.autovividict import countdict, autovividict

class TestMakeDatestring(unittest.TestCase):
    def test_datestring(self):
        """Test that make_datestring produces output in the right form."""
        for (year, month, day, expected_result) in (
            (1, 2, 3, '0001-02-03'),
            (11, 2, 3, '0011-02-03'),
            (111, 2, 3, '0111-02-03'),
            (1111, 2, 3, '1111-02-03'),
            (1, 12, 3, '0001-12-03'),
            (11, 12, 3, '0011-12-03'),
            (111, 12, 3, '0111-12-03'),
            (1111, 12, 3, '1111-12-03'),
            (1, 2, 13, '0001-02-13'),
            (11, 2, 13, '0011-02-13'),
            (111, 2, 13, '0111-02-13'),
            (1111, 2, 13, '1111-02-13'),
            (1, 12, 13, '0001-12-13'),
            (11, 12, 13, '0011-12-13'),
            (111, 12, 13, '0111-12-13'),
            (1111, 12, 13, '1111-12-13'),
            ):
            computed_result = make_datestring(year, month, day)
            self.assertTrue(computed_result == expected_result)

class TestFilenameFromURL(unittest.TestCase):
    def test_quoting(self):
        """Test that filename_from_url quotes URLs properly."""
        url = 'http://example.org/123#%23'
        filename = filename_from_url(url)
        self.assertTrue(filename == 'http%3A%2F%2Fexample.org%2F123%23%2523')

class TestCountdict(unittest.TestCase):
    def test_addition(self):
        """Test that a countdict serves as neutral element for addition."""
        c = countdict()
        c += 1
        self.assertTrue(c == 1)

    def test_dictionary(self):
        """Test that a countdict serves as a dictionary."""
        c = countdict()
        c['k'] = 'v'
        self.assertTrue('k' in c.keys())
        self.assertTrue('v' in c.values())
        self.assertTrue(('k', 'v') in c.items())

class TestAutovividict(unittest.TestCase):
    def test_autovivication(self):
        """Test that autovividict creates countdict as needed."""
        a = autovividict()
        a['k0'] = 'abc'
        a['k1'] += 1111
        a['k2']['k20'] = 'def'
        a['k2']['k21'] += 2222
        for k in 'k0', 'k1', 'k2':
            self.assertTrue(k in a.keys())
        for v in 'abc', 1111:
            self.assertTrue(v in a.values())
        for k, v in (
            ('k0', 'abc'),
            ('k1', 1111),
            ):
            self.assertTrue((k, v) in a.items())
        for k in 'k20', 'k21':
            self.assertTrue(k in a['k2'].keys())
        for v in 'def', 2222:
            self.assertTrue(v in a['k2'].values())
        for k, v in (
            ('k20', 'def'),
            ('k21', 2222),
            ):
            self.assertTrue((k, v) in a['k2'].items())

class TestMediaWiki(unittest.TestCase):
    def test_get_wiki_name(self):
        """Test if mediawiki helper can get wiki name."""
        wiki_name = mediawiki.get_wiki_name()
        self.assertTrue(wiki_name == 'Wikimedia Commons')

class TestMediaWikiTemplate(unittest.TestCase):
    def test_escape(self):
        """Test that template._escape escapes “=” and “|” as needed."""
        for (text, expected_result) in (
            ('abc = 123', 'abc {{=}} 123'),
            ('def | ghi', 'def {{!}} ghi'),
            ):
            computed_result = template._escape(text)
            self.assertTrue(computed_result == expected_result)

    def test_trim(self):
        """Test that template._trim removes whitespace properly."""
        expected_result = "The quick brown fox jumps over the lazy dog."
        for text in (
            "The quick brown fox jumps over the lazy dog.",
            "The quick brown fox jumps over the lazy dog. ",
            " The quick brown fox jumps over the lazy dog.",
            " The quick brown fox jumps over the lazy dog. ",
            "The  quick  brown  fox  jumps  over  the  lazy  dog.  ",
            "  The  quick  brown  fox  jumps  over  the  lazy  dog.",
            "  The  quick  brown  fox  jumps  over  the  lazy  dog.  ",
            "The quick brown  fox  jumps   over   the    lazy    dog.  ",
            ):
            computed_result = template._trim(text)
            self.assertTrue(computed_result == expected_result)

    def test_capitalize_properly(self):
        """Test that template._capitalize_properly capitalizes properly."""
        for (word, expected_output) in (
            ('a', 'a'),
            ('A', 'A'),
            ('ape', 'ape'),
            ('Ape', 'ape'),
            ('DNA', 'DNA'),
            ('HeLa', 'HeLa')
            ):
            calculated_output = template._capitalize_properly(word)
            self.assertTrue(calculated_output == expected_output)

    def test_postprocess_category(self):
        """Test for proper category postprocessing."""
        for (category, expected_output) in (
            # example categories
            ('blurb (blarb)', 'Blurb'),
            ('blurb, blarbed', 'Blarbed blurb'),
            ('blarb-Based blurb', 'Blarb-based blurb'),
            # real categories taken from <http://commons.wikimedia.org/wiki/File:-Adrenergic-Inhibition-of-Contractility-in-L6-Skeletal-Muscle-Cells-pone.0022304.s001.ogv>
            ('CHO Cells', 'CHO cells'),
            ('Beta-2 Adrenergic Receptors', 'Beta-2 adrenergic receptors'),
            ('Protein Kinases, Cyclic AMP-Dependent', 'Cyclic AMP-dependent protein kinases'),
            ):
            calculated_output = template._postprocess_category(category)
            self.assertTrue(calculated_output == expected_output)

    def test_get_license_template(self):
        for (url, expected_output) in (
            (u'http://creativecommons.org/licenses/by/2.0/',
             '{{cc-by-2.0}}'),
            (u'http://creativecommons.org/licenses/by-sa/2.0/',
             '{{cc-by-sa-2.0}}'),
            (u'http://creativecommons.org/licenses/by/2.5/',
             '{{cc-by-2.5}}'),
            (u'http://creativecommons.org/licenses/by-sa/2.5/',
             '{{cc-by-sa-2.5}}'),
            (u'http://creativecommons.org/licenses/by/3.0/',
             '{{cc-by-3.0}}'),
            (u'http://creativecommons.org/licenses/by-sa/3.0/',
             '{{cc-by-sa-3.0}}'),
            (u'http://creativecommons.org/licenses/by/4.0/',
             '{{cc-by-4.0}}'),
            (u'http://creativecommons.org/licenses/by-sa/4.0/',
             '{{cc-by-sa-4.0}}')
            ):
            calculated_output = template.get_license_template(url)
            self.assertTrue(calculated_output == expected_output)

    def test_make_description(self):
        for (title, caption, expected_output) in (
            ('foo', 'bar', 'foo bar'),
            ('Supplementary Data', 'foo', 'foo'),
            ('Supplementary material', 'bar', 'bar'),
            ('Additional file 1', 'baz', 'baz')
            ):
            calculated_output = template.make_description(title, caption)
            self.assertTrue(calculated_output == expected_output)

class TestEfetch(unittest.TestCase):
    def test_download(self):
        """Test if efetch._get_file_from_url can download files."""
        f = efetch._get_file_from_url('http://example.org')
        self.assertTrue('Example Domain' in f.read())

    def test_get_pmcid_from_doi(self):
        """Test if efetch.get_pmcid_from_doi can retrieve correct PMCIDs."""
        for (doi, expected_pmcid) in (
            (u'10.1371/journal.pone.0062199', 3631234),
            (u'10.1371/journal.pone.0093036', 3973673),
            (u'10.1371/journal.pone.0099936', 4057317)
            ):
            retrieved_pmcid = efetch.get_pmcid_from_doi(doi)
            self.assertTrue(retrieved_pmcid == expected_pmcid)

    def test_get_pmid_from_doi(self):
        """Test if efetch.get_pmid_from_doi can retrieve correct PMIDs."""
        for (doi, expected_pmid) in (
            (u'10.1371/journal.pone.0062199', 23620812),
            (u'10.1371/journal.pone.0093036', 24695492),
            (u'10.1371/journal.pone.0099936', 24927280)
            ):
            retrieved_pmid = efetch.get_pmid_from_doi(doi)
            self.assertTrue(retrieved_pmid == expected_pmid)

    def test_get_categories_from_pmid(self):
        """Test if efetch.get_categories_from_pmid can retrieve categories."""
        retrieved_categories = efetch.get_categories_from_pmid(23620812)
        for category in ['Behavior, Animal', 'Calcium', 'Drosophila melanogaster', 'Embryo, Nonmammalian', 'Feedback, Sensory', 'Larva', 'Locomotion', 'Motor Neurons', 'Muscle Contraction', 'Nerve Net', 'Sensation', 'Sense Organs', 'Time Factors']:
            self.assertTrue(category in retrieved_categories)

if __name__ == '__main__':
    unittest.main()
