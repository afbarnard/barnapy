"""Sampling algorithms

Copyright (c) 2016 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.
"""

import itertools as itools
import random


def reservoir_sample(items, sample_size, prng=random):
    """Samples the given items without replacement.

    Works in one pass without knowing the number of items and so is
    suitable for use with iterables (unlike `random.sample`).  Returns
    the samples in a list (the "reservoir").  The returned reservoir is
    a genuine random sample of the given items but it is not guaranteed
    to be in a random order; shuffle it as needed.  If the sample size
    is larger than the number of items, then the reservoir will just
    include all the items.

    * items: Iterable of items.
    * sample_size: How many samples to return in the reservoir.
    * prng: The pseudo-random number generator to use.

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
    """Samples the given items just as in `reservoir_sample` but returns
    the sampled items in their original order.
    """
    # Sample enumerated items
    sample = reservoir_sample(enumerate(items), sample_size, prng)
    # Sort by index to restore the original order.  There will not be
    # ties among the indices so no need for a key function.
    sample.sort()
    # Return original items (the second object of each pair)
    return [pair[1] for pair in sample]
