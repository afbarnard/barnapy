"""Tests `logging.py`."""

# Copyright (c) 2023 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


import io
import unittest

from .. import logging


class FormattingStylesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Mute the output that would normally go to stderr
        cls._sink = io.StringIO()
        logging.basicConfig(
            level=logging.DEBUG,
            stream=cls._sink,
        )

    def test_get_root_logger(self):
        exp = logging._logging.getLogger()
        act = logging.getLogger()
        self.assertIs(exp, act)

    def test_loggers_w_different_formatting_styles(self):
        # Some experiments for what follows are contained in the log
        # message for commit 2c4522508efc in
        # <https://github.com/Ong-Research/aou_ovarcan/>.

        # Make loggers with default and other styles of formatting
        lgr_test = logging.getLogger('test')
        lgr_prcnt = logging.getLogger('test.prcnt', '%')
        lgr_brace = logging.getLogger('test.brace', '{')
        lgr_tmplt = logging.getLogger('test.tmplt', '$')
        # Attach a stream to the test logger
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(
            '{levelname} {name}: {message}', '%Y-%m-%dT%H:%M:%S', '{'))
        lgr_test.addHandler(handler)
        # Log a message with each style of formatting
        lgr_test.debug('%s', 11)
        lgr_prcnt.debug('%s', 13)
        lgr_brace.debug('{} & {num}', 17, num=19)
        lgr_tmplt.debug('${num}', 29, num=23)
        # Check the result
        exp = '''
DEBUG test: 11
DEBUG test.prcnt: 13
DEBUG test.brace: 17 & 19
DEBUG test.tmplt: 23
'''.lstrip()
        act = stream.getvalue()
        self.maxDiff = None
        self.assertEqual(exp, act)


class ParseLevelNameTest(unittest.TestCase):

    def test_none(self):
        sentinel = object()
        (lvl, err) = logging.parse_level_name(None, sentinel)
        self.assertIs(lvl, sentinel)
        self.assertIsNone(err)

    def test_non_string(self):
        sentinel = object()
        (lvl, err) = logging.parse_level_name(54321, sentinel)
        self.assertIs(lvl, sentinel)
        self.assertIsNotNone(err)

    def test_unrecognized(self):
        sentinel = object()
        (lvl, err) = logging.parse_level_name('asdf', sentinel)
        self.assertIs(lvl, sentinel)
        self.assertIsNotNone(err)

    def test_strip_whitespace(self):
        sentinel = object()
        (lvl, err) = logging.parse_level_name('\t fatal\n', sentinel)
        self.assertEqual(logging.FATAL, lvl)
        self.assertIsNone(err)
