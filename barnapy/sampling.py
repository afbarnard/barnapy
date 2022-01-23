"""Sampling algorithms."""


# Copyright (c) 2015-2016, 2020, 2022 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import itertools as itools
import random


def reservoir_sample(items, sample_size, prng=random):
    """Sample the given items without replacement and return them in a
    list (the "reservoir").

    Works in one pass without knowing the number of items and so is
    suitable for use with iterables (unlike `random.sample`).  The
    returned reservoir is a genuine random sample of the given items but
    it is not guaranteed to be in a random order; shuffle it as needed.
    If the sample size is larger than the number of items, then the
    reservoir will just include all the items.

    * items: Iterable
    * sample_size: How many samples to return in the reservoir
    * prng: The pseudo-random number generator to use

    References:
    * http://en.wikipedia.org/wiki/Reservoir_sampling
    * Vitter, J.S.  Random sampling with a reservoir.  1985.
      http://dl.acm.org/citation.cfm?doid=3147.3165
    * Vitter, J.S.  Faster methods for random sampling.  1984.
      http://dl.acm.org/citation.cfm?doid=358105.893
    """
    # Fill the reservoir
    items = iter(items)
    reservoir = list(itools.islice(items, sample_size))
    # Sample the remaining items with decreasing probability: always
    # replace an item from the reservoir with the current item with
    # probability `sampleSize / itemCount`.  The first item is seen
    # right away, hence 'itemCount' starts at `sampleSize + 1`.  If the
    # reservoir was not filled, then this loop will not execute as the
    # items iterator will be exhausted.
    for count, item in enumerate(items, start=(sample_size + 1)):
        replace_idx = prng.randrange(count)
        if replace_idx < sample_size:
            reservoir[replace_idx] = item
    return reservoir
    # TODO update to version that uses fewer random numbers


def reservoir_sample_in_order(items, sample_size, prng=random):
    """Sample the given items just as in `reservoir_sample` but return
    the sampled items in their original order.
    """
    # Sample enumerated items
    sample = reservoir_sample(enumerate(items), sample_size, prng)
    # Sort by index to restore the original order.  There will not be
    # ties among the indices so no need for a key function.
    sample.sort()
    # Return original items (the second object of each pair)
    return [pair[1] for pair in sample]


def repeatedly_call(func, times=None): # TODO move somewhere more appropriate
    """
    Repeatedly call the given function and yield its return value.

    Like `itertools.repeat` but makes calls instead of just returning an
    object.
    """
    n_calls = 0
    while times is None or n_calls < times:
        yield func()
        n_calls += 1


def rejection_sample(sample_generator, accept_sample, max_tries=None) -> (
        bool, int, object):
    """
    Generate samples until one is accepted or the number of tries runs
    out.  Return (success?, number of tries, sample).

    sample_generator: iterable[sample] | callable() -> sample

        Iterable of samples or callable that returns a sample.

    accept_sample: callable(sample) -> bool

        Function that determines whether to accept or reject a sample.

    max_tries: int

        How many samples to generate and reject before giving up and
        returning.
    """
    # Make an iterable of samples
    samples = None
    if callable(sample_generator):
        samples = iter(repeatedly_call(sample_generator, times=max_tries))
    elif hasattr(sample_generator, '__iter__'):
        samples = iter(sample_generator)
    else:
        raise ValueError('Not an iterable or callable: '
                         f'sample_generator = {sample_generator}')
    # Loop to generate samples until one is accepted or the number of
    # tries runs out
    n_tries = 0
    sentinel = object()
    sample = next(samples, sentinel)
    while sample is not sentinel and (max_tries is None or n_tries < max_tries):
        n_tries += 1
        if accept_sample(sample):
            return (True, n_tries, sample)
        sample = next(samples, sentinel)
    return (False, n_tries, None)
