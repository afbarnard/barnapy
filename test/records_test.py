"""Tests records.py

Copyright (c) 2016 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.
"""

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
