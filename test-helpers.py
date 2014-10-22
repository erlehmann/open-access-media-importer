#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from helpers.autovividict import countdict, autovividict

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
        a['k1'] += 1111
        a['k2']['k2'] += 2222
        self.assertTrue('k1' in a.keys())
        self.assertTrue(1111 in a.values())
        self.assertTrue(('k1', 1111) in a.items())
        self.assertTrue('k2' in a.keys())
        self.assertTrue('k2' in a['k2'].keys())
        self.assertTrue(2222 in a['k2'].values())
        self.assertTrue(('k2', 2222) in a['k2'].items())

if __name__ == '__main__':
    unittest.main()
