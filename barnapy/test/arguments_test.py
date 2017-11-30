"""
Tests `arguments.py`
"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import collections
import unittest

from .. import arguments


class ParseTest(unittest.TestCase):

    def test_empty_args(self):
        args = []
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual({}, kw_args)
        self.assertEqual([], idx_args)

    def test_positional(self):
        args = [str(n) for n in range(5)]
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual({}, kw_args)
        self.assertEqual(args, idx_args)

    def test_key_value(self):
        args = ['--one', '1', '--two', '2', '--tre', '3']
        keys_values = {
            'one': ['1'],
            'two': ['2'],
            'tre': ['3'],
        }
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual(keys_values, kw_args)
        self.assertEqual([], idx_args)

    def test_assignment(self):
        args = ['--one=1', '--two=2', '--tre=3', '--for=']
        keys_values = {
            'one': ['1'],
            'two': ['2'],
            'tre': ['3'],
            'for': [''],
        }
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual(keys_values, kw_args)
        self.assertEqual([], idx_args)

    def test_flags(self):
        args = ['--flag1', '--flag2', '--flag3']
        keys_values = {
            'flag1': [None],
            'flag2': [None],
            'flag3': [None],
        }
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual(keys_values, kw_args)
        self.assertEqual([], idx_args)

    def test_multiple_values(self):
        args = [
            '--f', '--f', '--k', 'v', '--k', '--f', '--k', 'v', '--k=v',
        ]
        keys_values = {
            'f': [None, None, None],
            'k': ['v', None, 'v', 'v'],
        }
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual(keys_values, kw_args)
        self.assertEqual([], idx_args)

    def test_mixed(self):
        args = [
            'subcmd', '--k1', 'v1', 'p1', '--f1', '--k2', 'v2', 'p2',
            '--f2', '--k3=v3', 'p3', 'p4', '--k1', 'v4', 'p5', '--k1',
            'v5', '--f2',
        ]
        keys_values = {
            'f1': [None],
            'f2': [None, None],
            'k1': ['v1', 'v4', 'v5'],
            'k2': ['v2'],
            'k3': ['v3'],
        }
        positional = ['subcmd', 'p1', 'p2', 'p3', 'p4', 'p5']
        kw_args, idx_args = arguments.parse(args)
        self.assertEqual(keys_values, kw_args)
        self.assertEqual(positional, idx_args)
