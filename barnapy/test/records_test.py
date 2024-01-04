"""Tests 'records.py'."""

# Copyright (c) 2016, 2023 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import io
import unittest

from .. import logging
from .. import records


class ReadRecordsFromCsvTest(unittest.TestCase):

    # CSV records that could be interpreted as events
    text = """
    # Comment, empty line above
    129, 75,9, a , yes
    3917,
    3791
    ,6160,7,9,,on

    # Valid events below
    9650, 67, f
    6406,32,d
    3128 , 75 , 7 , c , true
    755,97,e,y
    214,81,0,c,1.0
    """ # Whitespace-only non-empty line

    raw_records = (
        ['    129', ' 75', '9', ' a ', ' yes'],
        ['    3917', ''],
        ['    3791'],
        ['    ', '6160', '7', '9', '', 'on'],
        ['    9650', ' 67', ' f'],
        ['    6406', '32', 'd'],
        ['    3128 ', ' 75 ', ' 7 ', ' c ', ' true'],
        ['    755', '97', 'e', 'y'],
        ['    214', '81', '0', 'c', '1.0'],
        )

    @classmethod
    def setUpClass(cls):
        logging.default_config()

    def setUp(self):
        # Disable logging for records module
        # TODO replace with a mock logger to collect messages
        logging.getLogger(records.__name__).setLevel(100)

    def test_read_records_from_csv_raw(self):
        input = io.StringIO(self.text)
        expected = self.raw_records
        actual = tuple(records.read_records_from_csv(input))
        self.assertEqual(expected, actual)

    def test_read_records_from_csv(self):
        # Only accept records of length 3-5.  Strip fields of
        # whitespace.
        def record_constructor(fields):
            if not (3 <= len(fields) <= 5):
                raise ValueError("Bad number of fields")
            return [f.strip() for f in fields]
        input = io.StringIO(self.text)
        expected = tuple(
            [f.strip() for f in self.raw_records[i]]
            for i in (0, 4, 5, 6, 7, 8))
        actual = tuple(records.read_records_from_csv(
            input, record_constructor))
        self.assertEqual(expected, actual)


class HeaderTest(unittest.TestCase):

    def test_is_type(self):
        self.assertTrue(records.Header.is_type(int))
        self.assertTrue(records.Header.is_type((int, float)))
        self.assertTrue(records.Header.is_type(object))
        self.assertTrue(records.Header.is_type(type))
        self.assertFalse(records.Header.is_type(None))
        self.assertFalse(records.Header.is_type([int, float]))
        self.assertFalse(records.Header.is_type((int, None)))
        self.assertTrue(records.Header.is_type((int, type(None))))

    def test_has_instance(self):
        hdr = records.Header(
            ('int', int),
            ('flt', float),
            ('str', str),
            ('non', type(None)),
            ('tup', tuple),
            ('lst', list),
            ('num', (int, float)),
        )
        for (rec, exp) in [
                ((1, 2.0, '3', None, (), [], 7), True),
                ((1, 2.0, '3', None, (), [], 7.0), True),
                ((1, 2.0, '3', None, (), [], '7'), False),
                ((1.0, 2.0, '3', None, (), [], 7), False),
        ]:
            with self.subTest((rec, exp)):
                act = hdr.has_instance(rec)
                self.assertEqual(exp, act)


class RecordTest(unittest.TestCase):

    names = ('one', 'two', 'tre', 'for', 'fiv', 'six', 'sev', 'ate')
    values = (1, 'two', 3.0, 'four', None, 'sticks', 11, ())
    types = (int, str, float, str, type(None), str, int, tuple)

    def setUp(self):
        hdr = records.Header(names=self.names, types=self.types)
        self.rec = records.Record(hdr, list(self.values))

    def test_get_by_index(self):
        for idx in range(len(self.values)):
            self.assertEqual(self.values[idx], self.rec[idx], idx)

    def test_get_by_name(self):
        for (idx, name) in enumerate(self.names):
            self.assertEqual(self.values[idx], self.rec[name], name)

    def test_get_by_attribute(self):
        for (idx, name) in enumerate(self.names):
            self.assertEqual(self.values[idx], getattr(self.rec, name), name)

    def test_set_by_index(self):
        idxs = list(range(len(self.values)))
        for idx in idxs:
            self.rec[idx] = idx
        self.assertEqual(idxs, self.rec.values)

    def test_set_by_name(self):
        for (idx, name) in enumerate(self.names):
            self.rec[name] = idx
        self.assertEqual(list(range(len(self.values))), self.rec.values)

    def test_set_by_attribute(self):
        for (idx, name) in enumerate(self.names):
            setattr(self.rec, name, idx)
        self.assertEqual(list(range(len(self.values))), self.rec.values)
