# Fundamental data processing operations, utility functions for
# iterables, and other data tools
#
# Copyright (c) 2016 Aubrey Barnard.  This is free software.  See
# LICENSE for details.

import itertools as itools


# TODO implement the relational algebra operations as objects that can be applied to one or more records?  would allow composing operations

def select(items, predicate=None):
    """Generates the items for which the given predicate is true.

    This is the relational algebra selection of the given items.

    * items: Iterable of items.
    * predicate: Function determining whether to select an item.
    """
    return filter(predicate, items)

def project(items, fields):
    """Generates tuples with the given fields from the given items.

    This is the relational algebra projection of the given items.

    * items: Iterable of indexables (e.g. tuples).
    * fields: The indices of the fields to return in the desired order.
    """
    for item in items:
        yield tuple(item[i] for i in fields)

def count(items):
    """Counts the number of items.

    * items: Iterable of items.
    """
    # Return length if possible
    if hasattr(items, '__len__'):
        return len(items)
    # Count items
    c = 0
    for item in items:
        c += 1
    return c
# TODO implement count as an object that can pass through items as they are counted?

def firsts(items, key=None):
    """Generates the first occurrence of each unique item.

    * items: Iterable of items.
    * key: Function computing the key for each item.  The key determines
      whether an item is unique.  If key is 'None', the item is its own
      key.

    Uses memory proportional to the number of unique keys.
    """
    seen = set()
    for item in items:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            yield item

distinct = firsts

def filter_by_key(items, keys, key=None, include=True):
    """Generates items whose keys are included in the given keys (or
    excluded from the given keys).

    * items: Iterable of items.
    * keys: Iterable of keys.
    * key: Function computing the key for each item.  If `None`, the
      item is its own key.
    * include: Whether the filter should include the items with the
      given keys or exclude them.

    This is intended to mimic the SQL functionality "where name [not] in
    set".
    """
    keys = set(keys)
    for item in items:
        k = key(item) if key else item
        if (k in keys) == include:
            yield item

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
