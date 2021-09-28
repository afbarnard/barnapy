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
        keys2vals = {}
        for (key, val) in items:
            with self.subTest(f'_insert({key}, {val})'):
                (existed, old_val) = rt._insert(key, val)
                self.assertEqual(key in keys2vals, existed)
                self.assertEqual(keys2vals.get(key), old_val)
                keys2vals[key] = val
                self.assertEqual(len(keys2vals), len(rt))

    def _test__lookup_items(self, rt, items, keys=None):
        keys2vals = dict(items)
        if keys is None:
            keys = keys2vals.keys()
        for key in keys:
            with self.subTest(f'_lookup({key})'):
                (found, value, *_) = rt._lookup(key)
                exists = key in keys2vals
                self.assertEqual(exists, found)
                if exists:
                    self.assertEqual(keys2vals[key], value)
                else:
                    self.assertIn(value, (None, rt._sentinel))

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

    def test__insert_suffixes(self):
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

    def test__insert_prefixes(self):
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

    def test__insert_replaces(self):
        rt = trees.RadixTree()
        kvs = [
            ('b', 'B'),
            ('a', 'A'),
            ('r', 'R'),
            ('n', 'N'),
            ('b', 'Б'),
            ('a', '∀'),
            ('r', 'Я'),
            ('n', 'И'),
        ]
        self._test__insert_items(rt, kvs)

    def test__lookup(self):
        kvs = [
            ('123456', 123456),
            ('123321', 123321),
            ('123456789', 123456789),
            ('2358', 2358),
        ]
        keys = [
            '987',      # Divergence at root
            '1235',     # Divergence at internal node
            '11235813', # Divergence at start of stored key extension
            '2359',     # Divergence within stored key extension
            '23589',    # Suffixes stored key
            '12345',    # Prefixes stored key
            '123',      # Matches internal node with no value (not found)
            '123456',   # Matches internal node with value (found)
        ]
        rt = trees.RadixTree(kvs)
        self._test__lookup_items(rt, kvs, keys)

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

    def test__visit_items(self):
        kvs = [
            ('underwear', 2),
            ('underwater', 3),
            ('underscore', 4),
            ('under', 1),
            ('undo', 5),
            ('tuna', 6),
            ('tune', 7),
            ('tone', 9),
            ('tome', 11),
            ('ton', 8),
            ('tonne', 10),
            ('', 0),
        ]
        rt = trees.RadixTree(kvs)
        exp = sorted(kvs, key=lambda kv: kv[1])
        act = list(rt._visit_items())
        self.assertEqual(exp, act)

    def test_sorted_items(self):
        kvs = [
            ('affable', 12),
            ('aardvark', 1),
            ('artwork', 15),
            ('ably', 7),
            ('abates', 3),
            ('abnormal', 6),
            ('affine', 13),
            ('abattoir', 4),
            ('after', 14),
            ('aberrant', 5),
            ('ab', 2),
            ('ad', 9),
            ('addles', 10),
            ('acceded', 8),
            ('aeons', 11),
            ('', 0),
        ]
        rt = trees.RadixTree(kvs)
        exp = sorted(kvs)
        act = list(rt._visit_items(sort=True))
        self.assertEqual(exp, act)

    def test_update(self):
        kvs = [
            ('some', 'one'),
            ('keys', 'vals'),
        ]
        rt = trees.RadixTree(kvs)
        self._test__lookup_items(rt, kvs)
        rt.update(kvs, some='where', keys='slav')
        rt.update(some='how')
        kvs = [
            ('some', 'how'),
            ('keys', 'slav'),
        ]
        self._test__lookup_items(rt, kvs)

    def test__delete(self):
        # Scenarios:
        # * delete nonexistent
        # * delete leaf
        # * delete internal (split) node (key is prefix of other keys)
        # * delete root
        kvs = [
            ('abcd', 'efgh'), # Branch 1
            ('ab', 'ba'),     # Split
            ('abba', 'baab'), # Branch 2
            ('z', 'a'),       # Other at root
            ((), ()),         # Empty key
        ]
        rt = trees.RadixTree(kvs)
        ks2vs = dict(kvs)
        # Delete nonexistent
        with self.subTest(f"_delete('fa')"):
            existed, old_val = rt._delete('fa')
            self.assertFalse(existed)
            self.assertIsNone(old_val)
            self.assertEqual(len(ks2vs), len(rt))
        # Delete existent until empty
        for (key, val) in kvs:
            with self.subTest(f'_delete({key})'):
                existed, old_val = rt._delete(key)
                self.assertTrue(existed)
                self.assertEqual(ks2vs[key], old_val)
                del ks2vs[key]
                self.assertEqual(len(ks2vs), len(rt))
        # Check that internal structure is empty
        self.assertEqual(0, len(rt._root))
        self.assertIsNone(rt._empty_key)
        self.assertEqual(rt._sentinel, rt._empty_key_value)
