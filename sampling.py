# Sampling algorithms

import itertools as itools
import random


def reservoir_sample(iterable, sample_size, prng=random):
    items = iter(iterable)
    reservoir = list(itools.islice(items, sample_size))
    for count, item in enumerate(items, start=(sample_size + 1)):
        replace_idx = random.randrange(count)
        if replace_idx < sample_size:
            reservoir[replace_idx] = item
    return reservoir

def reservoir_sample_in_order(iterable, sample_size, prng=random):
    items = iter(iterable)
    reservoir = list(enumerate(itools.islice(items, sample_size)))
    for count, item in enumerate(items, start=(sample_size + 1)):
        replace_idx = random.randrange(count)
        if replace_idx < sample_size:
            reservoir[replace_idx] = (count, item)
            # count is 1 ahead of the index, but that won't matter for
            # sorting
    reservoir.sort()
    return [pair[1] for pair in reservoir]
