"""Tests `sampling.py`."""

# Copyright (c) 2022 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import unittest

from .. import sampling


class RepeatedlyCallTest(unittest.TestCase):

    def test_times(self):
        range_itr = iter(range(10))
        self.assertEqual(
            list(sampling.repeatedly_call(lambda: next(range_itr), times=5)),
            list(range(5)))


class RejectionSampleTest(unittest.TestCase):

    def test_empty_generator(self):
        self.assertEqual(sampling.rejection_sample((), lambda sample: True),
                         (False, 0, None))

    def test_iterable_generator(self):
        self.assertEqual(
            sampling.rejection_sample(range(10), lambda sample: sample > 8),
            (True, 10, 9))
        self.assertEqual(
            sampling.rejection_sample(range(10), lambda sample: sample > 9),
            (False, 10, None))

    def test_callable_generator(self):
        range_itr = iter(range(10))
        self.assertEqual(
            sampling.rejection_sample(
                lambda: next(range_itr), lambda sample: sample > 8),
            (True, 10, 9))
        range_itr = iter(range(10))
        self.assertEqual(
            sampling.rejection_sample(
                lambda: next(range_itr), lambda sample: sample > 9, 10),
            (False, 10, None))

    def test_max_tries(self):
        self.assertEqual(
            sampling.rejection_sample(range(10), lambda sample: sample > 5, 3),
            (False, 3, None))
        self.assertEqual(
            sampling.rejection_sample(range(10), lambda sample: sample > 5, 7),
            (True, 7, 6))
