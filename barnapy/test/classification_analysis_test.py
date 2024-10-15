"""Tests 'classification_analysis.py'."""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import math
import unittest

from .. import classification_analysis as ca


class Table2x2Test(unittest.TestCase):

    def test_classification_properties(self):
        t1 = ca.Table2x2.from_cls(tp=1, fp=5, fn=8, tn=2)
        self.assertEqual(1, t1.tp)
        self.assertEqual(5, t1.fp)
        self.assertEqual(8, t1.fn)
        self.assertEqual(2, t1.tn)
        self.assertEqual(6, t1.pp)
        self.assertEqual(10, t1.pn)
        self.assertEqual(9, t1.p)
        self.assertEqual(7, t1.n)
        self.assertEqual(16, t1.all)

    def test_exposure_outcome_properties(self):
        t1 = ca.Table2x2.from_eos(yeyo=6, yeno=3, neyo=7, neno=2)
        self.assertEqual(6, t1.yeyo)
        self.assertEqual(3, t1.yeno)
        self.assertEqual(7, t1.neyo)
        self.assertEqual(2, t1.neno)
        self.assertEqual(9, t1.ye)
        self.assertEqual(9, t1.ne)
        self.assertEqual(13, t1.yo)
        self.assertEqual(5, t1.no)
        self.assertEqual(18, t1.all)

    def test___repr___from_cls(self):
        self.assertEqual('Table2x2(tp=2, fp=3, fn=1, tn=0)',
                         repr(ca.Table2x2.from_cls(2, 3, 1, 0)))

    def test_from_pppa(self):
        t1 = ca.Table2x2.from_2x2(5, 0, 1, 9)
        t2 = ca.Table2x2.from_pppa(5, 5, 6, 15)
        self.assertEqual(t1, t2)

    def test___neg__(self):
        tz = ca.Table2x2(0, 0, 0, 0)
        t1 = ca.Table2x2(1, 2, 3, 4)
        t2 = ca.Table2x2(-1, -2, -3, -4)
        self.assertEqual(tz, -tz)
        self.assertEqual(t1, -t2)
        self.assertEqual(-t1, t2)
        self.assertEqual(t1, -(-t1))

    def test___add__(self):
        tz = ca.Table2x2(0, 0, 0, 0)
        t1 = ca.Table2x2(1, 2, 3, 4)
        t2 = ca.Table2x2(5, 6, 7, 8)
        t3 = ca.Table2x2(6, 8, 10, 12)
        self.assertEqual(tz, tz + tz)
        self.assertEqual(t1, t1 + tz)
        self.assertEqual(t1, tz + t1)
        self.assertEqual(t3, t1 + t2)
        self.assertEqual(t3, t2 + t1)

    def test___sub__(self):
        tz = ca.Table2x2(0, 0, 0, 0)
        t1 = ca.Table2x2(1, 2, 3, 4)
        t2 = ca.Table2x2(8, 7, 6, 5)
        t3 = ca.Table2x2(7, 5, 3, 1)
        self.assertEqual(tz, tz - tz)
        self.assertEqual(t1, t1 - tz)
        self.assertEqual(-t1, tz - t1)
        self.assertEqual(t3, t2 - t1)

    def test_smoothed(self):
        t1 = ca.Table2x2(1, 2, 3, 4)
        t2 = ca.Table2x2(1.25, 2.25, 3.25, 4.25)
        self.assertEqual(t2, t1.smoothed(0.25))

    def test_tuple_2x2(self):
        t1 = ca.Table2x2(1, 2, 3, 4)
        self.assertEqual(((1, 3), (4, 2)), t1.tuple_2x2())

    def test_from_tuple_2x2(self):
        t1 = ca.Table2x2(1, 2, 3, 4)
        self.assertEqual(t1, ca.Table2x2.from_tuple_2x2(t1.tuple_2x2()))

    def test_tuple_3x3(self):
        t1 = ca.Table2x2(1, 2, 3, 4)
        self.assertEqual(((1, 3, 4), (4, 2, 6), (5, 5, 10)), t1.tuple_3x3())

    def test_from_tuple_3x3(self):
        t1 = ca.Table2x2(1, 2, 3, 4)
        self.assertEqual(t1, ca.Table2x2.from_tuple_3x3(t1.tuple_3x3()))


class Table2x2ScoresTest(unittest.TestCase):

    def setUp(self):        # tp, tn, fp, fn
        self.zero = ca.Table2x2(0, 0, 0, 0)
        self.poor = ca.Table2x2(3, 1, 9, 7)
        self.even = ca.Table2x2(5, 5, 5, 5)
        self.good = ca.Table2x2(8, 9, 2, 1)

    def test_tpr(self):
        self.assertEqual(-123, self.zero.tpr(default=-123))
        self.assertEqual(3/10, self.poor.tpr())
        self.assertEqual(5/10, self.even.tpr())
        self.assertEqual(8/ 9, self.good.tpr())

    def test_tnr(self):
        self.assertEqual(-123, self.zero.tnr(default=-123))
        self.assertEqual(1/10, self.poor.tnr())
        self.assertEqual(5/10, self.even.tnr())
        self.assertEqual(9/11, self.good.tnr())

    def test_fpr(self):
        self.assertEqual(-123, self.zero.fpr(default=-123))
        self.assertEqual(9/10, self.poor.fpr())
        self.assertEqual(5/10, self.even.fpr())
        self.assertEqual(2/11, self.good.fpr())

    def test_fnr(self):
        self.assertEqual(-123, self.zero.fnr(default=-123))
        self.assertEqual(7/10, self.poor.fnr())
        self.assertEqual(5/10, self.even.fnr())
        self.assertEqual(1/ 9, self.good.fnr())

    def test_ppv(self):
        self.assertEqual(-123, self.zero.ppv(default=-123))
        self.assertEqual(3/12, self.poor.ppv())
        self.assertEqual(5/10, self.even.ppv())
        self.assertEqual(8/10, self.good.ppv())

    def test_npv(self):
        self.assertEqual(-123, self.zero.npv(default=-123))
        self.assertEqual(1/ 8, self.poor.npv())
        self.assertEqual(5/10, self.even.npv())
        self.assertEqual(9/10, self.good.npv())

    def test_fdr(self):
        self.assertEqual(-123, self.zero.fdr(default=-123))
        self.assertEqual(9/12, self.poor.fdr())
        self.assertEqual(5/10, self.even.fdr())
        self.assertEqual(2/10, self.good.fdr())

    def test_fxr(self):
        self.assertEqual(-123, self.zero.false_omission_rate(default=-123))
        self.assertEqual(7/ 8, self.poor.false_omission_rate())
        self.assertEqual(5/10, self.even.false_omission_rate())
        self.assertEqual(1/10, self.good.false_omission_rate())

    def test_accuracy(self):
        self.assertEqual(-1234, self.zero.accuracy(default=-1234))
        self.assertEqual( 4/20, self.poor.accuracy())
        self.assertEqual(10/20, self.even.accuracy())
        self.assertEqual(17/20, self.good.accuracy())

    def test_balanced_accuracy(self):
        self.assertEqual(-1, self.zero.balanced_accuracy(default=-1))
        self.assertEqual((3/10 + 1/10) / 2, self.poor.balanced_accuracy())
        self.assertEqual((5/10 + 5/10) / 2, self.even.balanced_accuracy())
        self.assertEqual((8/ 9 + 9/11) / 2, self.good.balanced_accuracy())

    def test_f_beta(self):
        for beta in (0.5, 2):
            beta_sqrd = beta * beta
            beta_sqrd_p1 = beta_sqrd + 1
            self.assertEqual(-1, self.zero.f_beta(beta=beta, default=-1))
            self.assertEqual(
                (beta_sqrd_p1 * 3/12 * 3/10) / (beta_sqrd * 3/12 + 3/10),
                self.poor.f_beta(beta=beta))
            self.assertEqual(
                (beta_sqrd_p1 * 5/10 * 5/10) / (beta_sqrd * 5/10 + 5/10),
                self.even.f_beta(beta=beta))
            self.assertEqual(
                (beta_sqrd_p1 * 8/10 * 8/9) / (beta_sqrd * 8/10 + 8/9),
                self.good.f_beta(beta=beta))

    def test_f1(self):
        self.assertEqual(-1, self.zero.f1(default=-1))
        self.assertAlmostEqual(
            (2 * 3/12 * 3/10) / (3/12 + 3/10), self.poor.f1(), delta=1e-15)
        self.assertAlmostEqual(
            (2 * 5/10 * 5/10) / (5/10 + 5/10), self.even.f1(), delta=1e-15)
        self.assertAlmostEqual(
            (2 * 8/10 * 8/ 9) / (8/10 + 8/ 9), self.good.f1(), delta=1e-15)


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
        mi = ca.binary_mutual_information(1, 1, 1, 1)
        self.assertAlmostEqual(0.0, mi, places=10)

    def test_independent(self):
        #   1    0
        # 1 0.14 0.56 0.7
        # 0 0.06 0.24 0.3
        #   0.2  0.8
        mi = ca.binary_mutual_information(14, 56, 6, 24)
        self.assertAlmostEqual(0.0, mi, places=10)
        exp = (mit(15, 72, 22, 104) + mit(57, 72, 82, 104) +
               mit( 7, 32, 22, 104) + mit(25, 32, 82, 104))
        act = ca.binary_mutual_information(15, 57, 7, 25)
        self.assertAlmostEqual(exp, act, places=10)

    def test_positively_correlated(self):
        #   1    0
        # 1 0.95 0.03 0.98
        # 0 0.01 0.01 0.02
        #   0.96 0.04
        exp = (
            0.95 * math.log(0.95 / (0.98 * 0.96))
            + 0.03 * math.log(0.03 / (0.98 * 0.04))
            + 0.01 * math.log(0.01 / (0.02 * 0.96))
            + 0.01 * math.log(0.01 / (0.02 * 0.04)))
        act = ca.binary_mutual_information(95, 3, 1, 1)
        self.assertAlmostEqual(exp, act, places=10)
        exp = (mit(96, 100, 98, 104) + mit(4, 100, 6, 104) +
               mit( 2,   4, 98, 104) + mit(2,   4, 6, 104))
        act = ca.binary_mutual_information(96, 4, 2, 2)
        self.assertAlmostEqual(exp, act, places=10)

    def test_negatively_correlated(self):
        #   1    0
        # 1 0.09 0.42 0.51
        # 0 0.26 0.23 0.49
        #   0.35 0.65
        exp = (
            0.09 * math.log(0.09 / (0.51 * 0.35))
            + 0.42 * math.log(0.42 / (0.51 * 0.65))
            + 0.26 * math.log(0.26 / (0.49 * 0.35))
            + 0.23 * math.log(0.23 / (0.49 * 0.65)))
        act = ca.binary_mutual_information(9, 42, 26, 23)
        self.assertAlmostEqual(exp, act, places=10)
        exp = (mit(10, 53, 37, 104) + mit(43, 53, 67, 104) +
               mit(27, 51, 37, 104) + mit(24, 51, 67, 104))
        act = ca.binary_mutual_information(10, 43, 27, 24)
        self.assertAlmostEqual(exp, act, places=10)

    def test_equal(self):
        #   1    0
        # 1 0.09 0    0.09
        # 0 0    0.91 0.91
        #   0.09 0.91
        exp = (0.09 * math.log(0.09 / (0.09 * 0.09)) +
               0.91 * math.log(0.91 / (0.91 * 0.91)))
        act = ca.binary_mutual_information(9, 0, 0, 91)
        self.assertAlmostEqual(exp, act, places=10)
        exp = (mit(10, 11, 11, 104) + mit( 1, 11, 93, 104) +
               mit( 1, 93, 11, 104) + mit(92, 93, 93, 104))
        act = ca.binary_mutual_information(10, 1, 1, 92)
        self.assertAlmostEqual(exp, act, places=10)

    def test_zero(self):
        mi = ca.binary_mutual_information(0, 0, 0, 0, default=-1)
        self.assertAlmostEqual(-1, mi, places=10)

    def _test_corner_ones(self): # TODO
        pass

    def test_mit(self):
        exp = 0.33 * math.log(0.33 / (0.67 * 0.10))
        act = mit(33, 67, 10, 100)
        self.assertAlmostEqual(exp, act, places=10)


class RelativeRiskTest(unittest.TestCase):

    def test_ones(self):
        rr = ca.relative_risk(1, 1, 1, 1)
        self.assertAlmostEqual(1, rr, places=10)

    def test_uniform(self):
        rr = ca.relative_risk(123.4, 123.4, 123.4, 123.4)
        self.assertAlmostEqual(1, rr, places=10)

    def test_less_than_one(self):
        exp = (1 / 5) / (9 / 15)  # 1/3
        act = ca.relative_risk(1, 4, 9, 6)
        self.assertAlmostEqual(exp, act, places=10)

    def test_more_than_one(self):
        exp = (9 / 9) / (6 / 9)  # 3/2
        act = ca.relative_risk(9, 0, 6, 3)
        self.assertAlmostEqual(exp, act, places=10)

    def test_all_zero(self):
        rr = ca.relative_risk(0, 0, 0, 0, default=-1)
        self.assertAlmostEqual(-1, rr, places=10)

    def test_yeyo_zero(self):
        rr = ca.relative_risk(0, 0, 3, 7)
        self.assertAlmostEqual(0, rr, places=10)
        rr = ca.relative_risk(0, 3, 9, 4)
        self.assertAlmostEqual(0, rr, places=10)

    def test_neyo_zero(self):
        rr = ca.relative_risk(6, 7, 0, 0)
        self.assertAlmostEqual(float('inf'), rr, places=10)
        rr = ca.relative_risk(9, 9, 0, 6)
        self.assertAlmostEqual(float('inf'), rr, places=10)

    def test_yeyo_neyo_zero(self):
        rr = ca.relative_risk(0, 5, 0, 5)
        self.assertAlmostEqual(1, rr, places=10)
        rr = ca.relative_risk(0, 5, 0, 0)
        self.assertAlmostEqual(1, rr, places=10)
        rr = ca.relative_risk(0, 0, 0, 5)
        self.assertAlmostEqual(1, rr, places=10)

    def test_yeno_neno_zero(self):
        rr = ca.relative_risk(8, 0, 1, 0)
        self.assertAlmostEqual(1, rr, places=10)


# TODO test odds_ratio
# TODO test absolute_risk_difference
