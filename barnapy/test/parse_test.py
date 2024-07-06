"""Tests `parse.py`."""

# Copyright (c) 2020, 2023-2024 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import datetime
import fractions
import itertools as itools
import math
import re
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

    # Fractions
    frac_strs = [
        f'{sign}{num1}/{num2}'
        for sign in ('', '+', '-')
        # Basic integers with leading and trailing zeros
        for num1 in ('0', '1', '001', '100', '123456789')
        for num2 in ('1', '001', '100', '123456789')
    ]

    not_frac_strs = [
        f'{sign}{num1}/{num2}'
        for sign in ('', '+', '-')
        for num1 in ('', '1', 'e', '123abc')
        for num2 in ('', '1', '+1', '-1', 'e', '123abc')
        if num1 != '1' or num2 != '1'
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

    def test_frac_strs(self):
        self._test_python_parses(fractions.Fraction, self.frac_strs)

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
            self.frac_strs, self.not_frac_strs,
            self.flt_strs, self.not_flt_strs,
            self.inf_strs, self.nan_strs)

    def test_fraction(self):
        self._test_matches(parse.fraction_pattern, self.frac_strs)

    def test_not_fraction(self):
        self._test_non_matches(
            parse.fraction_pattern, self.not_frac_strs,
            self.int_strs, self.not_int_strs,
            self.flt_strs, self.not_flt_strs,
            self.inf_strs, self.nan_strs)

    def test_float(self):
        self._test_matches(parse.float_pattern, self.flt_strs)

    def test_not_float(self):
        self._test_non_matches(
            parse.float_pattern, self.not_flt_strs,
            self.frac_strs, self.not_frac_strs,
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


class DateTimePatternsTest(unittest.TestCase):

    date_ymd_strs = [
        f'{sign}{year}{sep}{month}{sep}{day}'
        for year in ['0', '0000']
        for month in ['0', '00']
        for day in ['0', '00']
        for sep in '/- .'
        for sign in ['', '+', '-']
    ]

    not_date_ymd_strs = [
        '-00-00', '-1-1-', '123-456-7890', '+1-123-456-7890',
        '20231222', '2023.12.222', '2023/123/22', '2023/12.22', '2023y12m22',
        '12/22/2023', '22-dec-2023', '2O23_12_22',
    ]

    time_strs = [
        f'{hours}{sep}{minutes}{ampm}{zone}'
        for hours in ['0', '00']
        for minutes in ['00']
        for sep in ':hH'
        for ampm in ['', 'am', ' P.M.']
        for zone in ['', '+1234', ' -9876']
    ] + [
        f'{hours}{seps[0]}{minutes}{seps[1]}{seconds}{fractions}{ampm}{zone}'
        for hours in ['0', '00']
        for minutes in ['00']
        for seconds in ['00']
        for fractions in ['', '.0', '.12345']
        for seps in ['::', 'hm', 'HM']
        for ampm in ['', 'am', ' P.M.']
        for zone in ['', '+1234', ' -9876']
    ]

    not_time_strs = [
        '000:00', '12:34:567', '12:34:56.',
        # TODO? '12h34:56', '12:34m56',
        '12:34:56 a.m', '12:34:56pn', '12h34m56.am', '12:34:56.789 P.M',
        '12:34:56.789 AM +123', '12:34:56.789 p.m. -12345',
    ]

    timedelta_strs = [
        f'{sign}{yr}{wk}{dy}{hr}{min}{sec}'
        for sign in ['', '-', '+']
        for yr in ['', '3y', '12.3 years ']
        for wk in ['', '22w', '92.4 weeks ']
        for dy in ['', '5d', '4.9 days ']
        for hr in ['', '12h', '3.21 hours ']
        for min in ['', '9m', '78.9 minutes ']
        for sec in ['', '1s', '12345.09876 seconds ']
    ]

    not_timedelta_strs = [
        '1y2w3d4h5ms', '1y 2w 3d 4h 5m s', '1', '+1', '-1', '1.1', '1.s',
        '-2.1ys', '+1.2 ys',
    ]

    def _test_matches(self, pattern, *strs):
        for txt in itools.chain.from_iterable(strs):
            with self.subTest(txt):
                self.assertIsNotNone(pattern.fullmatch(txt))

    def _test_non_matches(self, pattern, *strs):
        for txt in itools.chain.from_iterable(strs):
            with self.subTest(txt):
                self.assertIsNone(pattern.fullmatch(txt))

    def test_date_ymd(self):
        self._test_matches(parse.date_ymd_pattern, self.date_ymd_strs)

    def test_not_date_ymd(self):
        self._test_non_matches(
            parse.date_ymd_pattern, self.not_date_ymd_strs,
            self.time_strs, self.not_time_strs,
            self.timedelta_strs, self.not_timedelta_strs,
        )

    def test_time(self):
        self._test_matches(parse.time_pattern, self.time_strs)

    def test_not_time(self):
        self._test_non_matches(
            parse.time_pattern, self.not_time_strs,
            self.date_ymd_strs, self.not_date_ymd_strs,
            self.timedelta_strs, self.not_timedelta_strs,
        )

    def test_timedelta(self):
        self._test_matches(parse.timedelta_pattern, self.timedelta_strs)

    def test_not_timedelta(self):
        self._test_non_matches(
            parse.timedelta_pattern, self.not_timedelta_strs,
            self.date_ymd_strs, self.not_date_ymd_strs,
            self.time_strs, self.not_time_strs,
        )

    def test_is_timedelta(self):
        self.assertFalse(parse.is_timedelta(''))


class MkParseTest(unittest.TestCase):

    def test_mk_parse_numeric_empty_date_bool_none(self):
        texts = [
            '+123', '-31415926', '12d3',
            '3.1415926', '-1.23e-45', 'nAn', '-inF',
            '0001-01-01', '+2222+12+22', '2024-06-19',
            'true', 'FALSE', 'on', 'no',
            'none', 'NONE', 'null', 'na',
            '', '  ', '\t\v', '\r\n', '   .   ',
        ]
        try_construct = parse.mk_parse_numeric_empty_date_bool_none()
        vals = [try_construct(t, t)[1] for t in texts]
        self.assertEqual([123, -31415926, '12d3'], vals[0:3])
        self.assertEqual([3.1415926, -1.23e-45], vals[3:5])
        self.assertTrue(math.isnan(vals[5]))
        self.assertEqual(float('-inf'), vals[6])
        dt = datetime.date
        self.assertEqual([dt(1, 1, 1), dt(2222, 12, 22), dt(2024, 6, 19)],
                         vals[7:10])
        self.assertEqual([True, False, 'on', 'no'], vals[10:14])
        self.assertEqual([None, None, 'null', 'na'], vals[14:18])
        self.assertEqual([None, None, None, None, '   .   '], vals[18:23])


class CliCompoundLiteralsTest(unittest.TestCase):

    def test_cli_list_err(self):
        tests = [
            ('', []),
            ('one', ['one']),
            (' one ', ['one']),
            ('one,two', ['one', 'two']),
            (' one ; two ', ['one', 'two'],
             None, dict(split_pattern=re.compile(';'))),
            (' one , two ', [' one ', ' two '], None, dict(strip=False)),
            (' 0,1, 2 ,3 , 4 ', [0, 1, 2, 3, 4],
             None, dict(parse_item=parse.int_err)),
            (' 0 , 1 , 2 , tree3 ', [0, 1, 2],
             parse.SequenceParseError(
                 'Cannot parse an integer from', 'tree3', 3),
             dict(parse_item=parse.int_err)),
        ]
        for test_args in tests:
            with self.subTest(test_args):
                (text, exp, *args) = test_args
                exp_err = args[0] if len(args) >= 1 else None
                kwds = args[1] if len(args) >= 2 else {}
                (act, act_err) = parse.cli_list_err(text, **kwds)
                self.assertEqual(exp, act)
                self.assertEqual(
                    exp_err.__dict__ if exp_err is not None else None,
                    act_err.__dict__ if act_err is not None else None)

    def test_cli_kv_pair_err(self):
        tests = [
            ('', None, parse.ParseError(
                'Unable to split into a key and a value', '')),
            ('one', None, parse.ParseError(
                'Unable to split into a key and a value', 'one')),
            ('one:two', ('one', 'two')),
            (' one : two ', ('one', 'two')),
            (' one : two : tre ', ('one', 'two : tre')),
            (' one : two : tre ', (' one ', ' two : tre '), None,
             dict(strip=False)),
            ('one/two//tre/for', ('one/two', 'tre/for'), None,
             dict(split_pattern=re.compile('//'))),
            (' 1 : 2 ', (1, 2), None,
             dict(parse_key=parse.int_err, parse_val=parse.int_err)),
            (' 1 : 2.0 ', None,
             parse.ParseError('Cannot parse an integer from', '2.0'),
             dict(parse_key=parse.int_err, parse_val=parse.int_err)),
            (' 1.0 : 2.0 ', None,
             parse.ParseError('Cannot parse an integer from', '1.0'),
             dict(parse_key=parse.int_err, parse_val=parse.int_err)),
        ]
        for test_args in tests:
            with self.subTest(test_args):
                (text, exp, *args) = test_args
                exp_err = args[0] if len(args) >= 1 else None
                kwds = args[1] if len(args) >= 2 else {}
                (act, act_err) = parse.cli_kv_pair_err(text, **kwds)
                self.assertEqual(exp, act)
                self.assertEqual(
                    exp_err.__dict__ if exp_err is not None else None,
                    act_err.__dict__ if act_err is not None else None)

    def test_parse_cli_dict_err(self):
        tests = [
            ('', {}),
            ('one', {}, parse.SequenceParseError(
                'Unable to split into a key and a value', 'one', 0)),
            ('one:two', {'one': 'two'}),
            (' one : two , tre : for ', {'one': 'two', 'tre': 'for'}),
            (' one -- two --- tre -- for ', {'one': 'two', 'tre': 'for'},
             None, dict(item_split_pattern=re.compile('---'),
                        kv_split_pattern=re.compile('--'))),
            (' one : two , tre : for ', {' one ': ' two ', ' tre ': ' for '},
             None, dict(strip=False)),
            ('1: 1.0, 2: 2.0', {1: 1.0, 2: 2.0},
             None, dict(parse_key=parse.int_err,
                        parse_val=parse.float_err)),
            ('one:1, two:2, tre:tree3', dict(one=1, two=2),
             parse.SequenceParseError(
                 'Cannot parse an integer from', 'tree3', 2),
             dict(parse_val=parse.int_err)),
        ]
        for test_args in tests:
            with self.subTest(test_args):
                (text, exp, *args) = test_args
                exp_err = args[0] if len(args) >= 1 else None
                kwds = args[1] if len(args) >= 2 else {}
                (act, act_err) = parse.cli_dict_err(text, **kwds)
                self.assertEqual(exp, act)
                self.assertEqual(
                    exp_err.__dict__ if exp_err is not None else None,
                    act_err.__dict__ if act_err is not None else None)
