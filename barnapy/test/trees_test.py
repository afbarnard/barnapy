"""Tests `trees.py`."""

# Copyright (c) 2021 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


import unittest

from .. import trees


class RadixTreeTest(unittest.TestCase):

    def test_init_empty(self):
        rt = trees.RadixTree()
        self.assertEqual(0, len(rt))
        self.assertNotIn('a', rt)
        self.assertEqual([], list(rt))

    def _test__insert_items(self, rt, items):
        n_items = len(rt)
        for (key, val) in items:
            with self.subTest(f'_insert({key}, {val})'):
                (existed, old_val) = rt._insert(key, val)
                self.assertFalse(existed)
                self.assertIsNone(old_val)
                n_items += 1
                self.assertEqual(n_items, len(rt))

    def _test__lookup_items(self, rt, items):
        for (key, val) in items:
            with self.subTest(f'_lookup({key})'):
                (exists, value, *_) = rt._lookup(key)
                self.assertTrue(exists)
                self.assertIs(val, value)

    def test__insert__lookup_items_wo_common_prefix(self):
        rt = trees.RadixTree()
        kvs = ['1a', '2b', '3c']
        self._test__insert_items(rt, kvs)
        self._test__lookup_items(rt, kvs)

    def test__insert__lookup_items_w_common_prefix(self):
        rt = trees.RadixTree()
        kvs = [
            ('understanding', object()),
            ('underground', object()),
            ('undertake', object()),
        ]
        self._test__insert_items(rt, kvs)
        self._test__lookup_items(rt, kvs)
        self.assertNotIn('under', rt)

    def test_insert_suffix(self):
        rt = trees.RadixTree()
        kvs = [
            # Words that change meaning with added letters
            ('la', object()),
            ('lat', object()),
            ('lath', object()),
            ('lathe', object()),
            ('lather', object()),
            ('lathering', object()), # Well, not this one
        ]
        self._test__insert_items(rt, kvs)
        self._test__lookup_items(rt, kvs)

    def test_insert_prefix(self):
        rt = trees.RadixTree()
        kvs = [
            # Words that change meaning with removed letters
            ('lathering', object()),
            ('lather', object()), # Well, not this one
            ('lathe', object()),
            ('lath', object()),
            ('lat', object()),
            ('la', object()),
        ]
        self._test__insert_items(rt, kvs)
        self._test__lookup_items(rt, kvs)

    def test_none_as_key_and_value(self):
        rt = trees.RadixTree()
        kvs = [((None,), None)]
        self._test__insert_items(rt, kvs)
        self._test__lookup_items(rt, kvs)

    def test_empty_key(self):
        rt = trees.RadixTree()
        kvs = [('', object())]
        self._test__insert_items(rt, kvs)
        self._test__lookup_items(rt, kvs)
