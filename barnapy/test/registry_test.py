"""Tests 'registry.py'."""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


import unittest

from .. import registry


def _mk_cat(sep=''):
    def _cat(x1, x2):
        return f'{x1}{sep}{x2}'
    return _cat


class RootEntryTest(unittest.TestCase):

    def setUp(self):
        value = '_the_ value'
        entry = registry.RootEntry(value)
        reg = registry.HierarchicalRegistry('root entry').register_all([
            ('root', entry),
        ])
        self.value = value
        self.entry = entry
        self.reg = reg

    def test_value(self):
        self.assertEqual(self.value, self.reg.value('root'))

    def test_partial_value(self):
        self.assertEqual(
            self.value, self.reg.entry('root').partial_value(self.reg))

    def test_set_partial_value(self):
        value = 'the _new_ value'
        self.entry.set_partial_value(self.reg, value)
        self.assertEqual(value, self.reg.entry('root').partial_value(self.reg))


class AliasEntryTest(unittest.TestCase):

    def setUp(self):
        value = '_the_ value'
        reg = registry.HierarchicalRegistry('alias entry').register_all([
            ('root', registry.RootEntry(value)),
            ('base', registry.AliasEntry('root')),
            ('init', registry.AliasEntry('base')),
            ('seed', registry.AliasEntry('init')),
        ])
        self.value = value
        self.reg = reg

    def test_value(self):
        self.assertEqual(self.value, self.reg.value('seed'))

    def test_partial_value(self):
        self.assertEqual(
            self.value, self.reg.entry('seed').partial_value(self.reg))

    def test_set_partial_value(self):
        value = 'the _new_ value'
        self.reg.entry('seed').set_partial_value(self.reg, value)
        self.assertEqual(value, self.reg.entry('root').partial_value(self.reg))
        self.assertEqual(value, self.reg.value('seed'))


class DerivedValueEntryTest(unittest.TestCase):

    def test_overlay_dict(self):
        overlay_dict = registry.DerivedValueEntry.overlay_dict
        d1 = dict(a=1, b=2, c=3)
        d2 = dict(d=4, e=5)
        # Empty dicts and iterables
        self.assertEqual({}, overlay_dict({}, ()))
        self.assertEqual(d1, overlay_dict({}, d1))
        self.assertEqual(d2, overlay_dict(d2, ()))
        # Overlay dict
        self.assertEqual(dict(zip('abcde', range(1, 6))),
                         overlay_dict(d1, d2))
        # Overlay iterable and keyword arguments
        self.assertEqual(dict(zip('abcdef', range(1, 7))),
                         overlay_dict(d2, d1.items(), f=6))
        # Check originals not modified
        self.assertEqual(dict(a=1, b=2, c=3), d1)
        self.assertEqual(dict(d=4, e=5), d2)


class DynamicEntryTest(unittest.TestCase):

    def setUp(self):
        _cat = _mk_cat()
        self.reg = registry.HierarchicalRegistry('dynamic entry').register_all([
            ('a', registry.RootEntry('a')),
            ('b', registry.DynamicEntry('a', 'b', _cat)),
            ('c', registry.DynamicEntry('b', 'c', _cat)),
            ('d', registry.DynamicEntry('c', 'd', _cat)),
            ('e', registry.DynamicEntry('d', 'e', _cat)),
        ])

    def test_value(self):
        chars = 'abcde'
        for (idx, char) in enumerate(chars):
            self.assertEqual(chars[:(idx + 1)], self.reg.value(char))

    def test_partial_value(self):
        for char in 'abcde':
            self.assertEqual(
                char, self.reg.entry(char).partial_value(self.reg))

    def test_set_partial_value(self):
        self.reg.entry('a').set_partial_value(self.reg, 'A')
        self.assertEqual('Abcde', self.reg.value('e'))
        self.reg.entry('c').set_partial_value(self.reg, 'C')
        self.assertEqual('AbCde', self.reg.value('e'))
        self.reg.entry('e').set_partial_value(self.reg, 'E')
        self.assertEqual('AbCdE', self.reg.value('e'))


class StaticEntryTest(unittest.TestCase):

    def setUp(self):
        _cat = _mk_cat()
        self.reg = registry.HierarchicalRegistry('static entry').register_all([
            ('a', registry.RootEntry('A')),
            ('b', registry.StaticEntry('a', 'B', _cat)),
            ('c', registry.StaticEntry('b', 'C', _cat)),
            ('d', registry.StaticEntry('c', 'D', _cat)),
            ('e', registry.StaticEntry('d', 'E', _cat)),
        ])

    def test_value(self):
        keys = 'abcde'
        vals = keys.upper()
        # First the value is computed
        for (idx, key) in enumerate(keys):
            self.assertEqual(vals[:(idx + 1)], self.reg.value(key))
        # Then it is retrieved from saved
        for (idx, key) in enumerate(keys):
            self.assertEqual(vals[:(idx + 1)], self.reg.value(key))

    def test_set_partial_value(self):
        keys = 'abcde'
        vals = keys.upper()
        vals_new = vals.lower()
        # Compute all values
        for key in keys:
            self.reg.value(key)
        # Lowercase values one by one
        for (idx, key) in enumerate(keys[:-1]):
            self.reg.entry(key).set_partial_value(self.reg, vals[idx].lower())
            self.assertEqual(vals_new[:(idx + 1)], self.reg.value(key))
            self.assertEqual(vals[:(idx + 2)], self.reg.value(keys[idx + 1]))


class HierarchicalRegistryTest(unittest.TestCase):

    def test_basics(self):
        _dot_cat = _mk_cat('.')
        reg = registry.HierarchicalRegistry('basics').register_all([
            ('r', registry.RootEntry('R')),
            ('l1', registry.StaticEntry('r', 'L1', _dot_cat)),
            ('l2', registry.StaticEntry('r', 'L2', _dot_cat)),
        ])
        self.assertEqual(3, len(reg))
        self.assertIn('l2', reg)
        self.assertNotIn('l3', reg)
        self.assertEqual('r', reg.parent_key('l1'))
        self.assertEqual('R.L2', reg['l2'])
        self.assertEqual(['r', 'l1', 'l2'], list(reg))
        self.assertEqual(['r', 'l1', 'l2'], list(reg.keys()))
        self.assertEqual(['R', 'R.L1', 'R.L2'], list(reg.values()))
        self.assertEqual([('r', 'R'), ('l1', 'R.L1'), ('l2', 'R.L2')],
                         list(reg.items()))

    def test_get(self):
        reg = registry.HierarchicalRegistry('get').register_all([
            ('r', registry.RootEntry('R')),
        ])
        self.assertEqual('R', reg.get('r', 'Q'))
        self.assertEqual('Q', reg.get('s', 'Q'))

    def test_path(self):
        _dot_cat = _mk_cat('.')
        reg = registry.HierarchicalRegistry('path').register_all([
            ('a', registry.RootEntry('A')),
            ('b', registry.DynamicEntry('a', 'B', _dot_cat)),
            ('c', registry.DynamicEntry('b', 'C', _dot_cat)),
            ('d', registry.DynamicEntry('c', 'D', _dot_cat)),
            ('e', registry.DynamicEntry('d', 'E', _dot_cat)),
        ])
        keys = 'abcde'
        for (idx, key) in enumerate(keys):
            self.assertEqual(list(keys[:(idx + 1)]), reg.path(key))

    def test_register(self):
        reg = registry.HierarchicalRegistry('register')
        self.assertEqual(0, len(reg))
        self.assertNotIn('r', reg)
        reg.register('r', registry.RootEntry('R'))
        self.assertEqual(1, len(reg))
        self.assertIn('r', reg)
        self.assertEqual('R', reg['r'])

    def test_register__errors(self):
        reg = registry.HierarchicalRegistry('register')
        with self.assertRaises(registry.RegistryError):
            reg.register(None, registry.RootEntry('R'))
        reg.register('r', registry.RootEntry('R'))
        with self.assertRaises(registry.RegistryError):
            reg.register('r', registry.RootEntry('R'))
        with self.assertRaises(registry.RegistryError):
            reg.register('s', registry.DynamicEntry.Overrider('t', 'S'))

    def test_derivation_w_all_entries(self):
        _dot_cat = _mk_cat('.')
        reg = registry.HierarchicalRegistry('all entries').register_all([
            ('l0r1', registry.RootEntry('L0R1')),
            ('al0r1', registry.AliasEntry('l0r1')),
            ('l1d1', registry.DynamicEntry('al0r1', 'L1D1', _dot_cat)),
            ('al1d1', registry.AliasEntry('l1d1')),
            ('l2s1', registry.StaticEntry('al1d1', 'L2S1', _dot_cat)),
            ('al2s1', registry.AliasEntry('l2s1')),
            ('l0r2', registry.RootEntry('L0R2')),
            ('al0r2', registry.AliasEntry('l0r2')),
            ('l1s2', registry.StaticEntry('al0r2', 'L1S2', _dot_cat)),
            ('al1s2', registry.AliasEntry('l1s2')),
            ('l2d2', registry.DynamicEntry('al1s2', 'L2D2', _dot_cat)),
            ('al2d2', registry.AliasEntry('l2d2')),
        ])
        self.assertEqual('L0R1.L1D1.L2S1', reg['al2s1'])
        self.assertEqual('L0R2.L1S2.L2D2', reg['al2d2'])
        reg.entry('al0r1').set_partial_value(reg, './L0R1')
        reg.entry('al0r2').set_partial_value(reg, './L0R2')
        self.assertEqual('./L0R1.L1D1', reg['al1d1'])
        self.assertEqual('L0R1.L1D1.L2S1', reg['al2s1'])
        self.assertEqual('L0R2.L1S2.L2D2', reg['al2d2'])
        reg.entry('al2d2').set_partial_value(reg, '↑L2D2')
        self.assertEqual('L0R2.L1S2.↑L2D2', reg['al2d2'])
        reg.entry('al1d1').set_partial_value(reg, '↑L1D1')
        self.assertEqual('./L0R1.↑L1D1', reg['al1d1'])
        reg.entry('al2s1').set_partial_value(reg, '←L2S1')
        self.assertEqual('./L0R1.↑L1D1.←L2S1', reg['al2s1'])
        reg.entry('al1s2').set_partial_value(reg, '←L1S2')
        self.assertEqual('./L0R2.←L1S2.↑L2D2', reg['al2d2'])
