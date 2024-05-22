"""Tests 'statistics.py'."""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free software released under the MIT license.  See `LICENSE`
# for details.


import unittest

from .. import statistics as stats


class WeightsDensitiesTest(unittest.TestCase):

    def test_uniform(self):
        window = lambda i, v: (v - 2, v + 2)
        vals = list(range(10))
        exp = [(i, 1, 3, 5, 1/5) for i in range(10)]
        act = list(stats.weights_densities(vals, window))
        self.assertEqual(exp, act)


'''
        |
        |
        |         |
        | |       |
  |     | |   |   |
| | | | | |   |   |
0 1 2 3 4 5 6 7 8 9

5-window, full:
{2: 11, 3: 13, 4: 11, 5: 10, 6: 11, 7: 9}
5-window, edge:
{0: 4, 1: 5, 8: 6, 9: 6}
5-window, mirror:
{0: 7, 1: 6, 8: 10, 9: 8}, imagine edges @ 2 & 7: {2: 15, 3: 12, 6: 13, 7: 8}
5-window, prop:
{0: 6.67, 1: 6.25, 8: 7.5, 9: 10.0}, edges @2&7: {2: 13.33, 3: 13.75, 6: 13.75, 7: 8.33}
'''
