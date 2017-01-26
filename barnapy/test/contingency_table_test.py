"""Tests contingency_tables.py"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import math
import unittest

from .. import contingency_table as ct


class TwoByTwoTableTest(unittest.TestCase):

    def setUp(self):
        self.zero = ct.TwoByTwoTable(0, 0, 0, 0)
        self.one = ct.TwoByTwoTable(1, 1, 1, 1)
        self.tab1 = ct.TwoByTwoTable(3, 1, 2, 4)

    def test_construct_no_names(self):
        expected = (
            (1, 2, 3),
            (3, 4, 7),
            (4, 6, 10),
            )
        actual = ct.TwoByTwoTable(1, 2, 3, 4).table_3x3()
        self.assertEqual(expected, actual)

    def test_construct_2x2(self):
        expected = ct.TwoByTwoTable(1, 2, 3, 4).table_3x3()
        actual = ct.TwoByTwoTable(
            exp_out=1,
            exp_no_out=2,
            out_no_exp=3,
            no_exp_out=4,
            ).table_3x3()
        self.assertEqual(expected, actual)

    def test_construct_3x3_corners(self):
        expected = ct.TwoByTwoTable(1, 2, 3, 4).table_3x3()
        actual = ct.TwoByTwoTable(
            exp_out=1,
            exp_tot=3,
            out_tot=4,
            total=10,
            ).table_3x3()
        self.assertEqual(expected, actual)

    def test_exp_out(self):
        self.assertEqual(0, self.zero.exp_out)
        self.assertEqual(1, self.one.exp_out)
        self.assertEqual(3, self.tab1.exp_out)

    def test_exp_no_out(self):
        self.assertEqual(0, self.zero.exp_no_out)
        self.assertEqual(1, self.one.exp_no_out)
        self.assertEqual(1, self.tab1.exp_no_out)

    def test_out_no_exp(self):
        self.assertEqual(0, self.zero.out_no_exp)
        self.assertEqual(1, self.one.out_no_exp)
        self.assertEqual(2, self.tab1.out_no_exp)

    def test_no_exp_out(self):
        self.assertEqual(0, self.zero.no_exp_out)
        self.assertEqual(1, self.one.no_exp_out)
        self.assertEqual(4, self.tab1.no_exp_out)

    def test_exp_tot(self):
        self.assertEqual(0, self.zero.exp_tot)
        self.assertEqual(2, self.one.exp_tot)
        self.assertEqual(4, self.tab1.exp_tot)

    def test_no_exp_tot(self):
        self.assertEqual(0, self.zero.no_exp_tot)
        self.assertEqual(2, self.one.no_exp_tot)
        self.assertEqual(6, self.tab1.no_exp_tot)

    def test_out_tot(self):
        self.assertEqual(0, self.zero.out_tot)
        self.assertEqual(2, self.one.out_tot)
        self.assertEqual(5, self.tab1.out_tot)

    def test_no_out_tot(self):
        self.assertEqual(0, self.zero.no_out_tot)
        self.assertEqual(2, self.one.no_out_tot)
        self.assertEqual(5, self.tab1.no_out_tot)

    def test_total(self):
        self.assertEqual(0, self.zero.total)
        self.assertEqual(4, self.one.total)
        self.assertEqual(10, self.tab1.total)

    def test_smoothed(self):
        self.assertEqual(
            self.one.table_3x3(), self.zero.smoothed().table_3x3())
        expected = (
            (6, 4, 10),
            (5, 7, 12),
            (11, 11, 22),
            )
        actual = self.tab1.smoothed(pseudocount=3).table_3x3()
        self.assertEqual(expected, actual)

    def test_table_2x2(self):
        expected = (
            (3, 1),
            (2, 4),
            )
        actual = self.tab1.table_2x2()
        self.assertEqual(expected, actual)

    def test_table_3x3(self):
        expected = (
            (3, 1, 4),
            (2, 4, 6),
            (5, 5, 10),
            )
        actual = self.tab1.table_3x3()
        self.assertEqual(expected, actual)


class TemporalTwoByTwoTableTest(TwoByTwoTableTest):

    def setUp(self):
        self.zero = ct.TemporalTwoByTwoTable(0, 0, 0, 0, 0, 0)
        self.one = ct.TemporalTwoByTwoTable(0.7, 0.3, 1, 1, 1, 1)
        self.tab1 = ct.TemporalTwoByTwoTable(2, 1, 3, 1, 2, 4)

    def test_exp_bef_out(self):
        self.assertEqual(0, self.zero.exp_bef_out)
        self.assertAlmostEqual(0.7, self.one.exp_bef_out, places=10)
        self.assertEqual(2, self.tab1.exp_bef_out)

    def test_exp_aft_out(self):
        self.assertEqual(0, self.zero.exp_aft_out)
        self.assertAlmostEqual(0.3, self.one.exp_aft_out, places=10)
        self.assertEqual(1, self.tab1.exp_aft_out)

    def test_smoothed(self):
        expected = (
            (5, 3, 8),
            (4, 6, 10),
            (9, 9, 18),
            )
        smoothed = self.tab1.smoothed(pseudocount=2)
        actual = smoothed.table_3x3()
        self.assertEqual(expected, actual)
        self.assertEqual(3, smoothed.exp_bef_out)
        self.assertEqual(2, smoothed.exp_aft_out)

    def test_cohort_table(self):
        expected = (
            (2, 1, 3),
            (3, 4, 7),
            (5, 5, 10),
            )
        actual = self.tab1.cohort_table().table_3x3()
        self.assertEqual(expected, actual)


def mit(joint_count, marg1_count, marg2_count, total_count):
    """Return one term in the mutual information sum"""
    joint = joint_count / total_count
    marg1 = marg1_count / total_count
    marg2 = marg2_count / total_count
    return joint * math.log(joint / (marg1 * marg2))


class BinaryMutualInformationTest(unittest.TestCase):

    def test_independent_uniform(self):
        #   1    0
        # 1 0.25 0.25 0.5
        # 0 0.25 0.25 0.5
        #   0.5  0.5
        table = ct.TwoByTwoTable(1, 1, 1, 1)
        actual = ct.binary_mutual_information(table)
        self.assertAlmostEqual(0.0, actual, places=10)
        smoothed_table = table.smoothed(pseudocount=1)
        actual = ct.binary_mutual_information(smoothed_table)
        self.assertAlmostEqual(0.0, actual, places=10)

    def test_independent(self):
        #   1    0
        # 1 0.14 0.56 0.7
        # 0 0.06 0.24 0.3
        #   0.2  0.8
        table = ct.TwoByTwoTable(14, 56, 6, 24)
        actual = ct.binary_mutual_information(table)
        self.assertAlmostEqual(0.0, actual, places=10)
        expected = (mit(15, 72, 22, 104) + mit(57, 72, 82, 104)
                    + mit(7, 32, 22, 104) + mit(25, 32, 82, 104))
        smoothed_table = table.smoothed(pseudocount=1)
        actual = ct.binary_mutual_information(smoothed_table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_positively_correlated(self):
        #   1    0
        # 1 0.95 0.03 0.98
        # 0 0.01 0.01 0.02
        #   0.96 0.04
        table = ct.TwoByTwoTable(95, 3, 1, 1)
        expected = (
            0.95 * math.log(0.95 / (0.98 * 0.96))
            + 0.03 * math.log(0.03 / (0.98 * 0.04))
            + 0.01 * math.log(0.01 / (0.02 * 0.96))
            + 0.01 * math.log(0.01 / (0.02 * 0.04)))
        actual = ct.binary_mutual_information(table)
        self.assertAlmostEqual(expected, actual, places=10)
        expected = (mit(96, 100, 98, 104) + mit(4, 100, 6, 104)
                    + mit(2, 4, 98, 104) + mit(2, 4, 6, 104))
        smoothed_table = table.smoothed(pseudocount=1)
        actual = ct.binary_mutual_information(smoothed_table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_negatively_correlated(self):
        #   1    0
        # 1 0.09 0.42 0.51
        # 0 0.26 0.23 0.49
        #   0.35 0.65
        table = ct.TwoByTwoTable(9, 42, 26, 23)
        expected = (
            0.09 * math.log(0.09 / (0.51 * 0.35))
            + 0.42 * math.log(0.42 / (0.51 * 0.65))
            + 0.26 * math.log(0.26 / (0.49 * 0.35))
            + 0.23 * math.log(0.23 / (0.49 * 0.65)))
        actual = ct.binary_mutual_information(table)
        self.assertAlmostEqual(expected, actual, places=10)
        expected = (mit(10, 53, 37, 104) + mit(43, 53, 67, 104)
                    + mit(27, 51, 37, 104) + mit(24, 51, 67, 104))
        smoothed_table = table.smoothed(pseudocount=1)
        actual = ct.binary_mutual_information(smoothed_table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_equal(self):
        #   1    0
        # 1 0.09 0    0.09
        # 0 0    0.91 0.91
        #   0.09 0.91
        table = ct.TwoByTwoTable(9, 0, 0, 91)
        expected = (0.09 * math.log(0.09 / (0.09 * 0.09))
                    + 0.91 * math.log(0.91 / (0.91 * 0.91)))
        actual = ct.binary_mutual_information(table)
        self.assertAlmostEqual(expected, actual, places=10)
        expected = (mit(10, 11, 11, 104) + mit(1, 11, 93, 104)
                    + mit(1, 93, 11, 104) + mit(92, 93, 93, 104))
        smoothed_table = table.smoothed(pseudocount=1)
        actual = ct.binary_mutual_information(smoothed_table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_zero(self):
        table = ct.TwoByTwoTable(0, 0, 0, 0)
        actual = ct.binary_mutual_information(table)
        self.assertAlmostEqual(0.0, actual, places=10)
        smoothed_table = table.smoothed(pseudocount=1)
        actual = ct.binary_mutual_information(smoothed_table)
        self.assertAlmostEqual(0.0, actual, places=10)

    def test_mit(self):
        expected = 0.33 * math.log(0.33 / (0.67 * 0.10))
        actual = mit(33, 67, 10, 100)
        self.assertAlmostEqual(expected, actual, places=10)


class RelativeRiskTest(unittest.TestCase):

    def test_ones(self):
        table = ct.TwoByTwoTable(1, 1, 1, 1)
        expected = 1.0
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_uniform(self):
        table = ct.TwoByTwoTable(123.4, 123.4, 123.4, 123.4)
        expected = 1.0
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_less_one(self):
        table = ct.TwoByTwoTable(1, 4, 9, 6)
        expected = (1 / 5) / (9 / 15)  # 1/3
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_more_one(self):
        table = ct.TwoByTwoTable(9, 0, 6, 3)
        expected = (9 / 9) / (6 / 9)  # 3/2
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_zero(self):
        table = ct.TwoByTwoTable(0, 0, 0, 0)
        expected = 1.0
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_zero_exp_tot(self):
        table = ct.TwoByTwoTable(0, 0, 3, 7)
        expected = 0.0
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)
        table = ct.TwoByTwoTable(0, 3, 9, 4)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_zero_no_exp_tot(self):
        table = ct.TwoByTwoTable(6, 7, 0, 0)
        expected = float('inf')
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)
        table = ct.TwoByTwoTable(9, 9, 0, 6)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_zero_out_tot(self):
        table = ct.TwoByTwoTable(0, 5, 0, 5)
        expected = 1.0
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)

    def test_zero_no_out_tot(self):
        table = ct.TwoByTwoTable(8, 0, 1, 0)
        expected = 1.0
        actual = ct.relative_risk(table)
        self.assertAlmostEqual(expected, actual, places=10)
