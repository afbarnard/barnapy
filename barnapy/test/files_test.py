"""Tests `files.py`."""

# Copyright (c) 2023 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import io
import os
import tempfile
import unittest

from .. import files


class StreamTest(unittest.TestCase):

    def test_open__open_file(self):
        msg = "Hiya!  How're yoo?"
        open_file = tempfile.TemporaryFile('wt+', encoding='utf-8')
        with files.open(open_file, 'wt') as file:
            print(msg, file=file)
        self.assertFalse(open_file.closed)
        open_file.seek(0)
        contents = open_file.read()
        self.assertEqual(msg + '\n', contents)
        open_file.close()

    def test_open__stringio(self):
        msg = "Hiya!  How're yoo?"
        buff = io.StringIO()
        with files.open(buff, 'wt') as file:
            print(msg, file=file)
        self.assertFalse(buff.closed)
        contents = buff.getvalue()
        self.assertEqual(msg + '\n', contents)

    def test_open__pipe(self):
        msg = "Hiya!  How're yoo?"
        (pipe_r_fd, pipe_w_fd) = os.pipe()
        with open(pipe_w_fd, 'wt') as pipe_w:
            with files.open(pipe_w, 'wt') as file:
                print(msg, file=file)
            self.assertFalse(pipe_w.closed)
        with open(pipe_r_fd, 'rt') as pipe_r:
            contents = pipe_r.read()
            self.assertEqual(msg + '\n', contents)

    # TODO? test_open__stderr.  is it possible?
