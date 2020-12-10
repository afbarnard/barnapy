"""Sampling algorithms."""


# Copyright (c) 2015-2016, 2020 Aubrey Barnard.
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


def repeatedly_call(func, n_calls=None): # TODO move somewhere more appropriate
    """
    Repeatedly call the given function and yield its return value.

    Like `itertools.repeat` but makes calls instead of just returning an
    object.
    """
    call_idx = 0
    while n_calls is None or call_idx < n_calls:
        yield func()
        call_idx += 1


def rejection_sample( # TODO make into object that can track sampling progress
        generate_sample,
        accept_sample,
        n_samples=None,
        max_tries=None,
):
    samples = None
    if callable(generate_sample):
        samples = repeatedly_call(generate_sample)
    elif hasattr(generate_sample, '__iter__'):
        samples = generate_sample
    else:
        raise ValueError(
            f'Not a callable or iterable: {generate_sample}')
    sample_count = 0
    n_tries = 0
    # Generate samples indefinitely
    for sample in samples:
        # See if this sample is acceptable
        if accept_sample(sample):
            # Count the sample and yield it
            sample_count += 1
            # Have the counts reflect the sample at this point
            yield sample
            # Quit if generated enough samples
            if n_samples is not None and sample_count >= n_samples:
                return
            # Reset the number of tries
            n_tries = 0
        else:
            # The sample was rejected.  Try again.
            n_tries += 1
            # Quit if tried too many times
            if max_tries is not None and n_tries >= max_tries:
                raise Exception( # TODO have a proper exception
                    'Rejection sampling failed: too many tries')
    # TODO log warning that sample generator ran out before the desired number of samples was reached
