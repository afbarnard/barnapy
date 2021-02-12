"""Utilities for working with NumPy."""

# Copyright (c) 2021 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


# Needed for PEP 484-style type annotations
from __future__ import annotations # Python >= 3.7

import random

import numpy
import numpy.random


class NumpyAsStdlibPrng(random.Random):
    """
    Adapter to allow using a NumPy PRNG (`numpy.random.Generator`) as a
    standard library PRNG (`random.Random`).
    """
    # See https://github.com/numpy/numpy/blob/master/numpy/random/bit_generator.pyx

    def __init__(self, numpy_prng):
        """
        Construct a wrapper for the given `numpy.random.Generator` so that
        it behaves like a `random.Random`.
        """
        # `Random.__init__` calls `self.seed` which doesn't make sense here
        # because the given PRNG is already seeded.  Therefore, patch in
        # `seed` after superclass init.
        self.seed = super().seed # Hide local method
        super().__init__()
        self.seed = NumpyAsStdlibPrng.seed # Reinstate local method
        self._prng = numpy_prng

    def seed(self, seed):
        """
        Replace the underlying NumPy PRNG with a new one seeded with the
        given seed.

        It is better to just create a new `NumpyAsStdlibPrng` object
        with the desired generator constructed with the desired seed.
        """
        # Construct a new BitGenerator of the same type using reflection
        bit_gen = type(self._prng.bit_generator)(seed)
        self._prng = numpy.random.Generator(bit_gen)

    def getstate(self):
        return self._prng.bit_generator.state

    def setstate(self, state):
        self._prng.bit_generator.state = state

    def random(self):
        return self._prng.random()


def numpy_bit_generator(
        stdlib_prng:random.Random) -> numpy.random.BitGenerator:
    """
    Return a NumPy MT19937 bit generator initialized to the same
    internal state as the given `random.Random` (which is also a
    Mersenne twister PRNG).  The two PRNGs should generate the same
    sequence going forward.
    """
    # See https://github.com/python/cpython/blob/3.9/Lib/random.py
    version, state, gauss_next = stdlib_prng.getstate()
    assert len(state) == 625
    position = state[-1]
    state_array = numpy.array(state[:624], dtype=numpy.uint32)
    # See https://github.com/numpy/numpy/blob/master/numpy/random/_mt19937.pyx
    mt_bit_gen = numpy.random.MT19937()
    mt_bit_gen.state = {
        'bit_generator': mt_bit_gen.__class__.__name__,
        'state': {
            'key': state_array,
            'pos': position,
        },
    }
    return mt_bit_gen
