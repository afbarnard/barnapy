"""Auxiliary collections."""

# Copyright (c) 2020 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


class DefaultValueDict(dict):
    """
    A map that returns a default value for any unknown key.

    This allows efficiently representing mappings where most of the
    values are the same.
    """

    def __init__(self, *args, default=None, **kwds):
        super().__init__(*args, **kwds)
        self._dflt = default

    def __missing__(self, key):
        return self._dflt


# Sketch for later:
#class KeyedList:
#    """
#    List where items can also be (optionally) accessed by key.
#    """
#    # Construct API
#    def __init__(self, vals=None, *kvs, keys=None, vks=None, **kwds):
#        self._vals = []
#        self._key2idx = {}
#        TODO
#    # Read API
#    def n_keys(self):
#        return len(self._key2idx)
#    def n_values(self):
#        return len(self._vals)
#    def keys(self):
#        return self._key2idx.keys()
#    def values(self):
#        return iter(self._vals)
#    def keys_indices(self):
#        return self._key2idx.items()
#    def keys_indices_values(self):
#        for (key, idx) in self._key2idx.items():
#            yield (key, idx, self._vals[idx])
#    def indices_keyss(self):
#        NotImplemented
#    def values_indices_keyss(self):
#        NotImplemented
#    def has_index(self, index):
#        return isinstance(index, int) and 0 <= index < len(self)
#    def has_key(self, key):
#        return key in self._key2idx
#    def has_value(self, value):
#        return value in self._vals
#    def value_at(self, index):
#        return self._vals[index]
#    def value_of(self, key):
#        return self._vals[self._key2idx[key]]
#    def index_of(self, key):
#        return self._key2idx[key]
#    def keys_at(self, index):
#        """O(n_keys)"""
#        return (k for (k, i) in self._key2idx.items() if i == index)
#    def get(self, key, default=None):
#        """As for 'dict.get'."""
#        NotImplemented
#    # Object API
#    __repr__ = NotImplemented
#    __eq__ = NotImplemented
#    # Write API
#    add _kv
#    set _kv
#    del _kv
#    add_key
#    set_key
#    del_key
#    append _kv
#    extend _kvs
#    update
#    # Emulating lists
#    __len__ = n_values
#    __iter__ = values
#    __contains__ = has_value
#    def __getitem__(self, key):
#        if isinstance(key, int):
#            return self.value_at(key)
#        else:
#            return self.value_of(key)
#    __setitem__ = NotImplemented
#    __delitem__ = NotImplemented
