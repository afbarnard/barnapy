"""Tests 'combinatorics.py'."""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free software released under the MIT license.  See `LICENSE` for
# details.


import itertools as itools
import unittest

from .. import combinatorics


class BalancedSubsetsTest_RepeatedMinScore(unittest.TestCase):

    max_n_elements = 5 # TODO 6 or 10 once a formula for size2imbalance is worked out
    min_balance_level = 1

    def balanced_subsets(self, n_elements, subset_size, balance_level=None):
        return combinatorics.balanced_subsets__repeated_min_score(
            n_elements, subset_size, balance_level)

    def test_by_hand_10c3_10(self):
        """From red book p. 42."""
        exp = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 9), (1, 4, 6),
               (2, 5, 7), (1, 8, 9), (0, 4, 7), (2, 3, 6), (0, 5, 8)]
        act = list(itools.islice(self.balanced_subsets(10, 3), 10))
        self.assertEqual(exp, act)

    def test_by_hand_5c3_all(self):
        """From red book p. 43."""
        exp = [(0, 1, 2), (0, 3, 4), (1, 2, 3), (0, 1, 4), (2, 3, 4),
               (0, 1, 3), (0, 2, 4), (1, 2, 4), (0, 2, 3), (1, 3, 4)]
        act = list(self.balanced_subsets(5, 3))
        self.assertEqual(exp, act)

    @staticmethod
    def gen_bs_args(n_elements):
        for set_size in range(1, n_elements + 1):
            for subset_size in range(1, set_size + 1):
                for balance_level in range(1, subset_size + 1):
                    yield (set_size, subset_size, balance_level)

    def test_produces_combinations(self, max_n_elements=None):
        if max_n_elements is None:
            max_n_elements = self.max_n_elements
        for args in self.gen_bs_args(max_n_elements):
            (set_size, subset_size, balance_level) = args
            if balance_level < self.min_balance_level:
                continue
            exp = set(itools.combinations(range(set_size), subset_size))
            with self.subTest(args):
                act = set(self.balanced_subsets(*args))
                self.assertEqual(exp, act)

    @staticmethod
    def _counts_extrema(counts):
        extrema = {}
        for (subset, count) in counts.items():
            subset_size = len(subset)
            if subset_size in extrema:
                (min_count, max_count) = extrema[subset_size]
                if count < min_count:
                    extrema[subset_size] = (count, max_count)
                elif count > max_count:
                    extrema[subset_size] = (min_count, count)
            else:
                extrema[subset_size] = (count, count)
        return extrema

    @staticmethod
    def _mk_size2imbalance(subset_size):
        size2imb = {n: 2 for n in range(1, subset_size + 1)}
        size2imb[1] = 1
        size2imb[subset_size] = 1
        return size2imb

    def _check_balance(self, counts, ksubsets, size2imbalance):
        extrema = self._counts_extrema(counts)
        for (subset_size, (min_count, max_count)) in extrema.items():
            imbalance = size2imbalance[subset_size]
            # Pretty print info for evaluating the test if it fails
            srtd_counts = sorted(counts.items(), key=lambda kv: (len(kv[0]), kv[0], kv[1]))
            pprint_counts = ',\n '.join(f'{k}: {v}' for (k, v) in srtd_counts)
            self.assertLessEqual(
                max_count - min_count, imbalance,
                f'balance level {subset_size}: '
                f'{max_count} - {min_count} ≰ {imbalance}\n'
                f'ksubsets:\n{ksubsets}\ncounts:\n{{{pprint_counts}\n}}'
            )

    def test_balance(self, max_n_elements=None):
        if max_n_elements is None:
            max_n_elements = self.max_n_elements
        for args in self.gen_bs_args(max_n_elements):
            (set_size, subset_size, balance_level) = args
            if balance_level < self.min_balance_level:
                continue
            size2imbalance = self._mk_size2imbalance(subset_size)
            with self.subTest(args):
                ksubsets = list(self.balanced_subsets(*args))
                counts = {}
                for ksubset in ksubsets:
                    subsets = combinatorics._subsets(
                        ksubset, max_size=balance_level)
                    combinatorics._count_subsets(counts, subsets)
                    self._check_balance(counts, ksubsets, size2imbalance)


class BalancedSubsetsTest_RepeatedMinScore_NoDeleteAfterYield(
        BalancedSubsetsTest_RepeatedMinScore):

    min_balance_level = 2

    def balanced_subsets(self, n_elements, subset_size, balance_level=None):
        return combinatorics.balanced_subsets__repeated_min_score(
            n_elements, subset_size, balance_level, delete_after_yield=False)


class BalancedSubsetsTest_Heapq(BalancedSubsetsTest_RepeatedMinScore):

    def balanced_subsets(self, n_elements, subset_size, balance_level=None):
        return combinatorics.balanced_subsets__heapq(
            n_elements, subset_size, balance_level)
