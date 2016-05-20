# Data tools
#
# Copyright (c) 2016 Aubrey Barnard.  This is free software.  See
# LICENSE for details.

import itertools as itools


def map_reduce_by_key(items, mapper=None, reducer=None):
    """Maps and reduces items by key.  Returns an iterable of (key,
    reduced) pairs.

    The mapper must take an item and return a (key, value) pair.  The
    reducer must take an iterable of values and return an object.  The
    default mapper treats each item as its own key and value.  The
    default reducer collects the values in a tuple.
    """
    # Helper functions
    def identity_key_value(item):
        return (item, item)
    def first(indexable):
        return indexable[0]
    def second(indexable):
        return indexable[1]
    # Default arguments
    if mapper is None:
        mapper = identity_key_value
    if reducer is None:
        reducer = tuple
    # Transform items into (key, value) pairs
    mapped_items = map(mapper, items)
    # Group items by key and reduce
    for key, group in itools.groupby(
            sorted(mapped_items, key=first), key=first):
        # Run reducer on values only
        values = map(second, group)
        yield key, reducer(values)
