"""Tests contingencyTables.py"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


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
        self.zero = ct.TemporalTwoByTwoTable(0, 0, 0, 0, 0)
        self.one = ct.TemporalTwoByTwoTable(0.7, 0.3, 1, 1, 1)
        self.tab1 = ct.TemporalTwoByTwoTable(2, 1, 1, 2, 4)

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
