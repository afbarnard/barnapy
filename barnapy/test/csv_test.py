"""Tests 'csv.py'."""

# Copyright (c) 2023 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


import csv as pycsv
import io
import textwrap
import unittest

from .. import csv


class ParseFormatTest(unittest.TestCase):

# >>> ''.join((random.choice(',;.:|-\t '), random.choice('"\'`/'), random.choice('dDeE'), random.choice(' \\^~!'), random.choice('mMaAnNoO'), random.choice('kKtT'), random.choice('lLsS'), random.choice(['\n', '\r', '\r\n', '\n\r'])))

    def do_test(self, vals_specs, opt_key):
        for val_spec in vals_specs:
            (opt_val, spec) = val_spec
            format = csv.parse_format(spec)
            self.assertIn(opt_key, format)
            self.assertEqual(opt_val, format[opt_key], val_spec)

    def test_empty(self):
        self.assertEqual({}, csv.parse_format(''))

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
            csv.parse_format(',"f')

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
            csv.parse_format('|`D~P')

    def test_trim(self):
        vals_specs = [
            (False, ' `E!Mk'),
            (False, ";'e~AKs\r"),
            (True, ',/D^mtl\r'),
            (True, '-"e\\aT'),
        ]
        self.do_test(vals_specs, 'skipinitialspace')
        with self.assertRaises(ValueError):
            csv.parse_format(',"d~nS')

    def test_strict(self):
        vals_specs = [
            (False, ':`d mTl'),
            (False, " 'e mKL\n"),
            (True, ",'d~nks\r"),
            (True, '-/E OKS'),
        ]
        self.do_test(vals_specs, 'strict')
        with self.assertRaises(ValueError):
            csv.parse_format(" 'D~nkr")

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
        specs_formats = [
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
        for spec_dlct in specs_formats:
            (spec, dlct) = spec_dlct
            self.assertEqual(dlct, csv.parse_format(spec), spec_dlct)


class HeaderDetectionTest(unittest.TestCase):

    # Python's 'csv.reader' doesn't recognize a quote in the middle of a
    # field, even if it follows whitespace
    decls_hdr = textwrap.dedent('''
    id:int|dx_date| case?: int |" age: flt | int"|words:str
    1|2023-12-25|1|35.3|how's it going?
    2|2023-12-25|0|36.9|not too bad
    ''').lstrip()

    names_hdr = textwrap.dedent('''
    id|dx_date | case? | age|words
    3|2012-03-12|0|43.5|looks_like: a_type
    4|2012-03-12|1|44.6|no comment
    ''').lstrip()

    fake_hdr = textwrap.dedent('''
    version|3.14|2023-12-24|rc8|8 is great!
    5|2003-02-11|1|53.4|9 is fine.
    6|2003-02-11|0|51.1|7 is heaven!
    ''').lstrip()

    @staticmethod
    def _read_recs(text, csv_fmt='|"e\\mkl\n'):
        ifile = io.StringIO(text)
        fmt = csv.parse_format(csv_fmt)
        recs = list(pycsv.reader(ifile, **fmt))
        return recs

    def test_header_heuristic__declarations(self):
        for text_frac in [
                (self.decls_hdr, 5/5),
                (self.names_hdr, 5/5),
                (self.fake_hdr, 2/5),
        ]:
            with self.subTest(text_frac):
                (text, frac) = text_frac
                recs = self._read_recs(text)
                act = csv.header_heuristic__declarations(recs[0])
                self.assertEqual(frac, act)

    def test_header_heuristic__non_string_values(self):
        for text_frac in [
                (self.decls_hdr, 5/5),
                (self.names_hdr, 5/5),
                (self.fake_hdr, 3/5),
        ]:
            with self.subTest(text_frac):
                (text, frac) = text_frac
                recs = self._read_recs(text)
                act = csv.header_heuristic__non_string_values(recs[0])
                self.assertEqual(frac, act)

    def test_header_heuristic__names_values(self):
        for text_frac in [
                (self.decls_hdr, 4/5),
                (self.names_hdr, 4/5),
                (self.fake_hdr, 2/5),
        ]:
            with self.subTest(text_frac):
                (text, frac) = text_frac
                recs = self._read_recs(text)
                act = csv.header_heuristic__names_values(recs)
                self.assertEqual(frac, act)

    def test_score_header(self):
        for text_score in [
                (self.decls_hdr, (5 * 5/5 + 3 * 5/5 + 4 * 4/5) / 12), # 14/15
                (self.names_hdr, (5 * 5/5 + 3 * 5/5 + 4 * 4/5) / 12), # 14/15
                (self.fake_hdr,  (5 * 2/5 + 3 * 3/5 + 4 * 2/5) / 12), #  9/20
        ]:
            with self.subTest(text_score):
                (text, score) = text_score
                recs = self._read_recs(text)
                act = csv.score_header(recs)
                self.assertEqual(score, act)

    def test_detect_header(self):
        csv_fmt = csv.parse_format('|"e\\mkl\n')
        for text_hashdr in [
                (self.decls_hdr, True),
                (self.names_hdr, True),
                (self.fake_hdr, False),
        ]:
            with self.subTest(text_hashdr):
                (text, hashdr) = text_hashdr
                act = csv.detect_header(text, csv_fmt)
                self.assertEqual(hashdr, act[0])
                self.assertEqual(5, len(act[1]))
                self.assertIsNone(act[2])


class FieldSpecificationTest(unittest.TestCase):

    def test_parse(self):
        FS = csv.FieldSpecification
        ios = [
            # input, output, error

            # Basic pieces, standard order
            ('1', FS(1, None, None), None),
            ('lo', FS(None, 'lo', None), None),
            ('int', FS(None, None, int), None),
            ('999:X999', FS(999, 'X999', None), None),
            (' 7777777 : int ', FS(7777777, None, int), None),
            ('hi: float ', FS(None, 'hi', float), None),
            ('88: _123: bool', FS(88, '_123', bool), None),

            # Just separators
            ('', FS(None, None, None), None),
            (':', FS(None, None, None), None),
            ('::', FS(None, None, None), None),
            (':::', None, 'too many pieces'),

            # Permutations
            ('1:one:int', FS(1, 'one', int), None),
            ('one:int:1', FS(1, 'one', int), None),
            ('int:1:one', FS(1, 'one', int), None),
            ('1:int:one', FS(1, 'one', int), None),
            ('int:one:1', FS(1, 'one', int), None),
            ('one:1:int', FS(1, 'one', int), None),

            # Missing pieces
            ('2:two:', FS(2, 'two', None), None),
            ('2::bool', FS(2, None, bool), None),
            (':two:2', FS(2, 'two', None), None),
            ('two::bool', FS(None, 'two', bool), None),
            ('bool:2:', FS(2, None, bool), None),
            (':bool:two', FS(None, 'two', bool), None),

            # Ranges
            ('11-111 : X : str', FS(range(11, 112), 'X', str), None),

            # Union types
            ('num:int|float', FS(None, 'num', (int, float)), None),
            (' lo : bool | None ', FS(None, 'lo', (bool, type(None))), None),

            # Errors
            ('1, x, float', None, 'separator not specified'),
            ('0', None, 'not an ordinal'),
            ('-1', None, 'not positive'),
            ('3med', None, 'not a number'),
            ('3.21', None, 'not an integer'),
            (' 1 - 2 ', None, 'not a range'),
            ('object.member', None, 'not a (simple) name'),
            ('1:2:3', None, 'two numbers'),
            ('1:2-3', None, 'a number and a range'),
            ('lo:hi', None, 'two names'),
            ('field: int : float', None, 'two types'),
        ]
        for io in ios:
            with self.subTest(io):
                (text, exp_fs, exp_err) = io
                (act_fs, act_err) = csv.FieldSpecification.parse(text)
                if exp_err is None:
                    self.assertIsNone(act_err)
                    self.assertEqual(exp_fs, act_fs)
                else:
                    self.assertIsNotNone(act_err)

    def test_parse__sep(self):
        exp = csv.FieldSpecification(66, 'route', bool)
        (act, err) = csv.FieldSpecification.parse('bool, route, 66', sep=',')
        self.assertIsNone(err)
        self.assertEqual(exp, act)

    def test_parse__name_signifier(self):
        exp = csv.FieldSpecification(None, 'int', int)
        (act, err) = csv.FieldSpecification.parse(
            '!int:int', name_signifier='!')
        self.assertIsNone(err)
        self.assertEqual(exp, act)
        exp = csv.FieldSpecification(33, '33', None)
        (act, err) = csv.FieldSpecification.parse(
            '!!33:33', name_signifier='!!')
        self.assertIsNone(err)
        self.assertEqual(exp, act)
