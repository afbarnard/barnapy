"""Tests 'csv.py'."""

# Copyright (c) 2023 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


import csv as pycsv
import unittest

from .. import csv


class ParseCsvDialectTest(unittest.TestCase):

# >>> ''.join((random.choice(',;.:|-\t '), random.choice('"\'`/'), random.choice('dDeE'), random.choice(' \\^~!'), random.choice('mMaAnNoO'), random.choice('kKtT'), random.choice('lLsS'), random.choice(['\n', '\r', '\r\n', '\n\r'])))

    def do_test(self, vals_specs, opt_key):
        for val_spec in vals_specs:
            (opt_val, spec) = val_spec
            dialect = csv.parse_csv_dialect(spec)
            self.assertIn(opt_key, dialect)
            self.assertEqual(opt_val, dialect[opt_key], val_spec)

    def test_empty(self):
        self.assertEqual({}, csv.parse_csv_dialect(''))

    def test_delimiter(self):
        vals_specs = [
            (',', ','),
            (' ', ' '),
            ('-', '-`D!NtL\n'),
            ('\t', "\t'e\\MKS\r"),
        ]
        self.do_test(vals_specs, 'delimiter')

    def test_quote_character(self):
        vals_specs = [
            ("'", ",'"),
            ('`', ';`'),
            ('"', ':"D NkS\n\r'),
            ('/', '\t/e~OkL\n\r'),
        ]
        self.do_test(vals_specs, 'quotechar')

    def test_escaping_mode(self):
        vals_specs = [
            (False, ',"e'),
            (False, ':"E\\oTS\r'),
            (True, ',/d\\mKS\n'),
            (True, '\t/D'),
        ]
        self.do_test(vals_specs, 'doublequote')
        with self.assertRaises(ValueError):
            csv.parse_csv_dialect(',"f')

    def test_escape_character(self):
        vals_specs = [
            (None, '|`d '),
            (None, ';`d oTs\r\n'),
            ('\\', ';`D\\'),
            ('\\', ';`E\\NtS\n\r'),
            ('^', "|'d^ATS\n\r"),
        ]
        self.do_test(vals_specs, 'escapechar')

    def test_quoting_mode(self):
        vals_specs = [
            (pycsv.QUOTE_MINIMAL, ':`D\\m'),
            (pycsv.QUOTE_MINIMAL, "\t'd~MtL\r\n"),
            (pycsv.QUOTE_ALL, "|'E~aks\r\n"),
            (pycsv.QUOTE_ALL, " 'E!A"),
            (pycsv.QUOTE_NONE, ',`D~n'),
            (pycsv.QUOTE_NONE, "\t'e NkL\r"),
            (pycsv.QUOTE_NONNUMERIC, " 'D^okL\n\r"),
            (pycsv.QUOTE_NONNUMERIC, ".'D^O"),
        ]
        self.do_test(vals_specs, 'quoting')
        with self.assertRaises(ValueError):
            csv.parse_csv_dialect('|`D~P')

    def test_trim(self):
        vals_specs = [
            (False, ' `E!Mk'),
            (False, ";'e~AKs\r"),
            (True, ',/D^mtl\r'),
            (True, '-"e\\aT'),
        ]
        self.do_test(vals_specs, 'skipinitialspace')
        with self.assertRaises(ValueError):
            csv.parse_csv_dialect(',"d~nS')

    def test_strict(self):
        vals_specs = [
            (False, ':`d mTl'),
            (False, " 'e mKL\n"),
            (True, ",'d~nks\r"),
            (True, '-/E OKS'),
        ]
        self.do_test(vals_specs, 'strict')
        with self.assertRaises(ValueError):
            csv.parse_csv_dialect(" 'D~nkr")

    def test_eol(self):
        vals_specs = [
            ('\n', '-"D OKL\n'),
            ('\n\r', ":'d ots\n\r"),
            ('\r', ' /d~NKl\r'),
            ('\r\n', '\t`e\\OtS\r\n'),
            ('\n\n\n', ' /d\\aTl\n\n\n'),
        ]
        self.do_test(vals_specs, 'lineterminator')

    def test_doc_string_examples(self):
        specs_dialects = [
            (',"d mkl\r\n', dict(
                delimiter=',',
                quotechar='"',
                doublequote=True,
                escapechar=None,
                quoting=pycsv.QUOTE_MINIMAL,
                skipinitialspace=False,
                strict=False,
                lineterminator='\r\n',
            )),
            ('|"e\\mks\n', dict(
                delimiter='|',
                quotechar='"',
                doublequote=False,
                escapechar='\\',
                quoting=pycsv.QUOTE_MINIMAL,
                skipinitialspace=False,
                strict=True,
                lineterminator='\n',
            )),
            (' "E\\MTL\n\r', dict(
                delimiter=' ',
                quotechar='"',
                doublequote=False,
                escapechar='\\',
                quoting=pycsv.QUOTE_MINIMAL,
                skipinitialspace=True,
                strict=False,
                lineterminator='\n\r',
            )),
            ('\t"D OKS\r', dict(
                delimiter='\t',
                quotechar='"',
                doublequote=True,
                escapechar=None,
                quoting=pycsv.QUOTE_NONNUMERIC,
                skipinitialspace=False,
                strict=True,
                lineterminator='\r',
            )),
        ]
        self.maxDiff = None
        for spec_dlct in specs_dialects:
            (spec, dlct) = spec_dlct
            self.assertEqual(dlct, csv.parse_csv_dialect(spec), spec_dlct)
