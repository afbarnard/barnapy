"""Tests `numeric.py`."""

# Copyright (c) 2020 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import unittest

from .. import numeric


class NearestIntegersTest(unittest.TestCase):

    def test_round_down(self):
        reals = [1.3, 1.4]
        self.assertEqual([1, 1], numeric.nearest_integers(reals, 2))
        self.assertEqual([1, 2], numeric.nearest_integers(reals, 3))

    def test_round_up(self):
        reals = [1.9, 1.8]
        self.assertEqual([2, 2], numeric.nearest_integers(reals, 4))
        self.assertEqual([2, 1], numeric.nearest_integers(reals, 3))

    def test_rounded_recovers_exact(self):
        reals = [0.1, 2.3, 0.1, 3.2, 0.1, 4.9, 0.1]
        self.assertEqual([0, 2, 0, 3, 0, 5, 0],
                         numeric.nearest_integers(reals, 10))

    def test_budget_shortage(self):
        reals = [1.5, 1.5, 1.5, 5.5] # sum: 10
        # Rounded (half-even): [2, 2, 2, 6], sum: 12
        self.assertEqual([1, 1, 2, 6],
                         numeric.nearest_integers(reals, 10))

    def test_budget_excess(self):
        reals = [0.5, 0.5, 0.5, 8.5] # sum: 10
        # Rounded (half-even): [0, 0, 0, 8], sum: 8
        self.assertEqual([1, 1, 0, 8],
                         numeric.nearest_integers(reals, 10))

    def test_budget_makes_uniform_with_min_int(self):
        reals = [0.1, 0.1, 9.8]
        self.assertEqual([1, 1, 1],
                         numeric.nearest_integers(reals, 3, 1))

    @unittest.expectedFailure
    def test_decreasing_budget_min_int(self): # FIXME some subtleties / complications here
        reals = [0.5, 2.8, 0.5, 5.7, 0.5] # sum: 10
        # Rounded (half-even): [0, 3, 0, 6, 0], sum: 9
        # With min ints: [1, 3, 1, 6, 1], sum: 12
        budget2result = [
            (12, [1, 3, 1, 6, 1]),
            # Budget 12 diffs: [0.2, 0.3]
            (11, [1, 3, 1, 5, 1]),
            # Budget 11 diffs: [0.2, -0.7]
            (10, [1, 2, 1, 5, 1]),
            # Budget 10 diffs: [-0.8, -0.7]
            ( 9, [1, 2, 1, 4, 1]),
        ]
        for (budget, expected) in budget2result:
            with self.subTest(budget):
                self.assertEqual(
                    expected,
                    numeric.nearest_integers(reals, budget, 1))

    def test_negatives(self):
        reals = [0.1, -2.3, 0.1, -3.2, 0.1, -4.9, 0.1]
        self.assertEqual([0, -2, 0, -3, 0, -5, 0],
                         numeric.nearest_integers(reals, 10))

    def test_spike(self):
        reals = [0.1, -0.1, 0.1, 9.7]
        self.assertEqual([0, 0, 0, 10],
                         numeric.nearest_integers(reals, 10, 0))
        self.assertEqual([1, -1, 1, 7],
                         numeric.nearest_integers(reals, 10, 1))
