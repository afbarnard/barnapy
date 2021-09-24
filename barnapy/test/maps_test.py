"""Tests `maps.py`."""

# Copyright (c) 2021 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


import unittest

from .. import maps


class GenericMapTest:

    def kv_pairs(self):
        raise NotImplementedError('Override me in a subclass!')

    def construct_map(self, mapping=None, **kwargs):
        raise NotImplementedError('Override me in a subclass!')

    # Read #

    def test___len__(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        n_items = 0
        with self.subTest('empty map'):
            self.assertEqual(n_items, len(map_))
        with self.subTest('increasing length'):
            for (key, val) in kv_pairs:
                map_[key] = val
                n_items += 1
                self.assertEqual(n_items, len(map_), str((key, val)))
        with self.subTest('static length'):
            for (key, val) in kv_pairs:
                map_[key] = val
                self.assertEqual(n_items, len(map_), str((key, val)))
        with self.subTest('decreasing length'):
            for (key, val) in kv_pairs:
                del map_[key]
                n_items -= 1
                self.assertEqual(n_items, len(map_), str((key, val)))

    def test___contains__(self):
        # Test that half the keys exist and half do not
        kv_pairs = self.kv_pairs()
        half = len(kv_pairs) // 2
        assert half >= 1
        kv_pairs_in = kv_pairs[:half]
        kv_pairs_out = kv_pairs[half:]
        map_ = self.construct_map(kv_pairs_in)
        with self.subTest('contains'):
            for (key, val) in kv_pairs_in:
                self.assertIn(key, map_)
        with self.subTest('does not contain'):
            for (key, val) in kv_pairs_out:
                self.assertNotIn(key, map_)

    def test___getitem__(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        for (key, val) in kv_pairs:
            with self.subTest(f'key does not exist: {key}'):
                with self.assertRaises(KeyError):
                    map_[key]
            map_[key] = val
            with self.subTest(f'key exists: {key}'):
                self.assertIs(map_[key], val)

    def test_get(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        for (key, val) in kv_pairs:
            obj = object() # Unique object
            with self.subTest(f'key does not exist: {key}'):
                gotten = map_.get(key, obj)
                self.assertIs(gotten, obj)
            map_[key] = val
            with self.subTest(f'key exists: {key}'):
                gotten = map_.get(key, obj)
                self.assertIs(gotten, val)

    def test___iter__(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        with self.subTest('empty'):
            self.assertEqual(set(), set(map_))
        map_.update(kv_pairs)
        with self.subTest('nonempty'):
            self.assertEqual(set(k for (k, v) in kv_pairs), set(map_))

    def test_keys(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        with self.subTest('empty'):
            self.assertEqual(set(), set(map_.keys()))
        map_.update(kv_pairs)
        with self.subTest('nonempty'):
            self.assertEqual(set(k for (k, v) in kv_pairs), set(map_.keys()))

    def test_values(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        with self.subTest('empty'):
            self.assertEqual(set(), set(map_.values()))
        map_.update(kv_pairs)
        with self.subTest('nonempty'):
            self.assertEqual(set(v for (k, v) in kv_pairs), set(map_.values()))

    def items(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        with self.subTest('empty'):
            self.assertEqual(set(), set(map_.items()))
        map_.update(kv_pairs)
        with self.subTest('nonempty'):
            self.assertEqual(set(kv_pairs), set(map_.items()))

    # Write #

    def test___setitem__(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map()
        key, val1 = kv_pairs[0]
        val2 = kv_pairs[1][1]
        with self.subTest('insert'):
            map_[key] = val1
            self.assertEqual(1, len(map_))
            self.assertIs(map_[key], val1)
        with self.subTest('update'):
            map_[key] = val2
            self.assertEqual(1, len(map_))
            self.assertIs(map_[key], val2)

    def test_update(self):
        kv_pairs = self.kv_pairs()
        nm_v_pairs = {str(k): v for (k, v) in kv_pairs if str(k).isidentifier()}
        with self.subTest('mapping'):
            map_ = self.construct_map()
            map_.update(kv_pairs)
            self.assertEqual(len(kv_pairs), len(map_))
            self.assertEqual(set(kv_pairs), set(map_.items()))
        with self.subTest('kwargs'):
            map_ = self.construct_map()
            map_.update(**nm_v_pairs)
            self.assertEqual(len(nm_v_pairs), len(map_))
            self.assertEqual(set(nm_v_pairs.items()), set(map_.items()))
        with self.subTest('both mapping and kwargs'):
            map_ = self.construct_map()
            map_.update(kv_pairs, **nm_v_pairs)
            ks2vs = dict(kv_pairs)
            ks2vs.update(nm_v_pairs)
            self.assertEqual(len(ks2vs), len(map_))
            self.assertEqual(set(ks2vs.items()), set(map_.items()))

    def test___delitem__(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map(kv_pairs)
        n_items = len(kv_pairs)
        for (key, val) in kv_pairs:
            del map_[key]
            n_items -= 1
            self.assertEqual(n_items, len(map_))
            self.assertNotIn(key, map_)

    def test_clear(self):
        kv_pairs = self.kv_pairs()
        map_ = self.construct_map(kv_pairs)
        map_.clear()
        self.assertEqual(0, len(map_))
        for (key, val) in kv_pairs:
            self.assertNotIn(key, map_)
        self.assertEqual(set(), set(map_.items()))


class ListedPairsMapTest(unittest.TestCase, GenericMapTest):

    def kv_pairs(self):
        return [
            ('a', 'b'),
            ('b', 'a'),
            (0, 1),
            (1, 0),
            ('nun', None),
            (None, 'unu'),
            (object(), object()),
            ('badger', 'Bill'),
            ('bad', 'gerbil'),
        ]

    def construct_map(self, mapping=None, **kwargs):
        return maps.ListedPairsMap(mapping, **kwargs)


class SortedPairsMapTest(unittest.TestCase, GenericMapTest):

    def kv_pairs(self):
        return [
            ('a', 'b'),
            ('b', 'a'),
            ('0', 1),
            ('1', 0),
            ('nun', 'unu'),
            ('unu', 'nun'),
            ('None', None),
            ('object()', object()),
            ('badger', 'Bill'),
            ('bad', 'gerbil'),
        ]

    def construct_map(self, mapping=None, **kwargs):
        return maps.SortedPairsMap(mapping, **kwargs)


class ArrayMapTest(unittest.TestCase, GenericMapTest):

    def kv_pairs(self):
        return [
            (-97, 'a'),
            (-98, 'b'),
            (0, 1),
            (-1, 0),
            (-110, 'nun'),
            (-117, 'unu'),
            (-78, None),
            (-111, object()),
            (-2, 'badger Bill'),
            (-3, 'bad gerbil'),
        ]

    def construct_map(self, mapping=None, **kwargs):
        return maps.ArrayMap(key_lo=-127, size=128, mapping=mapping, **kwargs)
