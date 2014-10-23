#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from helpers import make_datestring, filename_from_url, efetch, mediawiki, \
    template
from helpers.autovividict import countdict, autovividict


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
                # real categories taken from
                # <http://commons.wikimedia.org/wiki/File:-Adrenergic-Inhibition-of-Contractility-in-L6-Skeletal-Muscle-Cells-pone.0022304.s001.ogv>
                ('CHO Cells', 'CHO cells'),
                ('Beta-2 Adrenergic Receptors', 'Beta-2 adrenergic receptors'),
                ('Protein Kinases, Cyclic AMP-Dependent',
                 'Cyclic AMP-dependent protein kinases'),
                ):
            calculated_output = template._postprocess_category(category)
            self.assertTrue(calculated_output == expected_output)

    def test_get_license_template(self):
        """Test for proper mapping of license URLs to license templates."""
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
        """Test for filtering of filler text when constructing description."""
        for (title, caption, expected_output) in (
                ('foo', 'bar', 'foo bar'),
                ('Supplementary Data', 'foo', 'foo'),
                ('Supplementary material', 'bar', 'bar'),
                ('Additional file 1', 'baz', 'baz')
                ):
            calculated_output = template.make_description(title, caption)
            self.assertTrue(calculated_output == expected_output)

if __name__ == '__main__':
    unittest.main()
