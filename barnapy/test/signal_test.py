"""Tests 'signal.py'."""

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
5-window, dens:
{0: 2.0, 1: 1.67, 2: 2.75, 3: 3.25, 4: 2.75, 5: 2.5, 6: 2.75, 7: 2.25, 8: 2.0, 9: 3.0}
3-window, dens:
{0: 3.0, 1: 2.0, 2: 2.0, 3: 4.0, 4: 5.0, 5: 4.5, 6: 2.5, 7: 1.0, 8: 3.0, 9: 4.0}
(1/4, 1/2, 1/4)-window, dens:
{0: 1.33, 1: 1.5, 2: 1.25, 3: 2.25, 4: 4.0, 5: 3.0, 6: 1.25, 7: 0.5, 8: 1.5, 9: 2.0}

[-0.27, 1.07, 1.20, 2.47, 2.78, 3.83, 3.95, 4.03, 4.07, 4.99, 5.38, 5.40, 6.91, 7.22, 8.78, 9.11, 9.11, 9.24]

±1, dens:           2.78           4.03      4.99                     8.78
[1/1, 2/2, 2/2, 2/2, 2/2, 4/2, 4/2, 5/2, 5/2, 5/2, 3/2, 3/2, 2/2, 2/2, 4/2, 4/2, 4/2, 4/2, 4/2]

±2, dens:                 2.78                     4.99
[3/2, 5/3.34, 5/3.47, 8/4, 8/4, 9/4, 9/4, 9/4, 9/4, 8/4, 9/4, 9/4, 6/4, 7/4, 6/2.46, 5/2.13, 5/2.13, 4/2]
'''
