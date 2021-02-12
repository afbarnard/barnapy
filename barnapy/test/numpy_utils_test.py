"""Tests `numpy_utils.py`."""

# Copyright (c) 2021 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import random
import unittest

import numpy.random

from .. import numpy_utils


class NumpyAsStdlibPrngTest(unittest.TestCase):

    def test_random_floats(self):
        seed = 0xdeadbeeffeedcafe
        n_samples = 10
        orig_prng = numpy.random.default_rng(seed)
        expected = [orig_prng.random() for _ in range(n_samples)]
        wrap_prng = numpy_utils.NumpyAsStdlibPrng(
            numpy.random.default_rng(seed))
        actual = [wrap_prng.random() for _ in range(n_samples)]
        self.assertEqual(expected, actual)


class NumpyBitGeneratorTest(unittest.TestCase):

    def test_random_floats(self):
        seed = 0xdeadbeeffeedcafe
        n_samples = 10
        old_prng = random.Random(seed)
        expected = [old_prng.random() for _ in range(n_samples)]
        new_prng = numpy.random.Generator(
            numpy_utils.numpy_bit_generator(
                random.Random(seed)))
        actual = [new_prng.random() for _ in range(n_samples)]
        self.assertEqual(expected, actual)
