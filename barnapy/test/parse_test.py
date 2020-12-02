"""Tests `parse.py`."""

# Copyright (c) 2020 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import itertools as itools
import math
import unittest

from .. import parse


class NumberPatternsTest(unittest.TestCase):

    # Integers
    int_strs = [
        f'{sign}{num}'
        for sign in ('', '+', '-')
        # Basic integers with leading and trailing zeros
        for num in ('0', '1', '001', '100', '123456789')
    ]

    not_int_strs = [
        f'{sign}{num}'
        for sign in ('', '+', '-')
        for num in ('', 'e', '123abc')
    ]

    # Floats
    flt_strs = [
        f'{sign}{whol}{frac}{exp}'
        for sign in ('', '+', '-')
        for whol in ('', '0', '1', '001', '100', '123456789')
        for frac in
        ['', *(f'.{num}'
               for num in ('', '0', '1', '001', '100', '123456789'))]
        for exp in
        ['', *(f'{exp}{sign}{num}'
               for exp in ('e', 'E')
               for sign in ('', '+', '-')
               for num in ('0', '02', '003', '1', '12', '123'))]
        if (whol and (frac or exp)) or len(frac) >= 2
    ]

    not_flt_strs = [
        f'{sign1}{num1}{dot}{num2}{exp}{sign2}{num3}'
        for sign1 in ('', '+', '-')
        for num1 in ('', '1', 'a', '1a')
        for dot in ('', '.', ':')
        for num2 in ('', '1', 'a', '1a')
        for exp in ('', 'e', 'f')
        for sign2 in ('', '+', '-')
        for num3 in ('', '1', 'a', '1a')
        if not (
            # Select all possible valid numbers
            num1 in ('', '1') and
            num2 in ('', '1') and
            num3 in ('', '1') and
            not (num1 == num2 == num3 == '') and
            (
                # Integers
                (dot == exp == '' and
                 (sign2 == '' or sign1 == num1 == num2 == ''))
                or
                # Floats without exponents
                (dot == '.' and exp == sign2 == '' and
                 (num1 == '1' or num2 == '1' or num3 == '1'))
                or
                # Floats with exponents
                (exp == 'e' and num3 == '1' and dot in ('', '.') and
                 (num1 == '1' or num2 == '1'))
            ))
    ]

    # Infinities
    inf_strs = [
        f'{sign}{num}'
        for sign in ('', '+', '-')
        for num in ('inf', 'Inf')
    ]

    # NaNs
    nan_strs = [
        f'{sign}{num}'
        for sign in ('', '+', '-')
        for num in ('nan', 'Nan', 'NaN')
    ]

    def _test_python_parses(self, num, *strs):
        for txt in itools.chain.from_iterable(strs):
            with self.subTest(txt):
                self.assertIsInstance(num(txt), num)

    def test_int_strs(self):
        self._test_python_parses(int, self.int_strs)

    def test_flt_strs(self):
        self._test_python_parses(float, self.flt_strs)

    def test_inf_strs(self):
        for txt in self.inf_strs:
            with self.subTest(txt):
                self.assertTrue(math.isinf(float(txt)))

    def test_nan_strs(self):
        for txt in self.nan_strs:
            with self.subTest(txt):
                self.assertTrue(math.isnan(float(txt)))

    def _test_matches(self, pattern, *strs):
        for txt in itools.chain.from_iterable(strs):
            with self.subTest(txt):
                self.assertIsNotNone(pattern.fullmatch(txt))

    def _test_non_matches(self, pattern, *strs):
        for txt in itools.chain.from_iterable(strs):
            with self.subTest(txt):
                self.assertIsNone(pattern.fullmatch(txt))

    def test_integer(self):
        self._test_matches(parse.integer_pattern, self.int_strs)

    def test_not_integer(self):
        self._test_non_matches(
            parse.integer_pattern, self.not_int_strs,
            self.flt_strs, self.not_flt_strs,
            self.inf_strs, self.nan_strs)

    def test_float(self):
        self._test_matches(parse.float_pattern, self.flt_strs)

    def test_not_float(self):
        self._test_non_matches(
            parse.float_pattern, self.not_flt_strs,
            self.int_strs, self.not_int_strs,
            self.inf_strs, self.nan_strs)


class RangePatternsTest(unittest.TestCase):

    def test_integer_range(self):
        # Ranges
        texts = ['0:0', '0:', ':0', ':', '-1:+1', '+1:-1',
                 '-{0}:+{0}'.format('0123456789')]
        for txt in texts:
            with self.subTest(txt):
                match = parse.integer_range_pattern.fullmatch(txt)
                self.assertIsNotNone(match)
                lohi = [n if n != '' else None for n in txt.split(':')]
                self.assertEqual(lohi, list(match.groups()))
        # Not ranges
        texts = ['0 : 0', '0.1:1.0', 'a:b', '-:+', '0:-', ':0:'
                 '1::1', '1:1:1', '-{0}:+{0}.'.format('0123456789')]
        for txt in texts:
            with self.subTest(txt):
                match = parse.integer_range_pattern.fullmatch(txt)
                self.assertIsNone(match)

    def test_float_range(self):
        # Ranges
        texts = ['.0:0.', '0.:', ':.0', ':', '1.:.1', '-1.0:+1.0',
                 '-1e-0:+1e+0',
                 '-{0}.{0}e-{0}:+{0}.{0}e+{0}'.format('0123456789')]
        for txt in texts:
            with self.subTest(txt):
                match = parse.float_range_pattern.fullmatch(txt)
                self.assertIsNotNone(match)
                lohi = [n if n != '' else None for n in txt.split(':')]
                self.assertEqual(lohi, list(match.groups()))
        # Not ranges
        texts = ['.0 : 0.', '1:1', 'e:e', '-:+', '0.:-', ':0.0:',
                 '1.0::0.1', '0.1:1.1:1.0',
                 '-{0}.{0}e-{0}:+{0}.{0}e+{0}.'.format('0123456789')]
        for txt in texts:
            with self.subTest(txt):
                match = parse.float_range_pattern.fullmatch(txt)
                self.assertIsNone(match)
