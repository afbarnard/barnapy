"""
Various implementations of maps based on arrays (not based on trees)
that avoid hashing.
"""

# Copyright (c) 2021 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


import bisect


class ListedPairsMap:
    """
    Map implemented as a list of key-value pairs.

    Good for storing a small number of items.  Does not use hashing.
    Follows the Python `dict` API.  Uses `==` for key equality, so
    beware of things like `0 == False`.

    Operation | Complexity
    ======================
    lookup    | O(n)
    insert    | O(n)
    delete    | O(n)
    length    | O(1)
    iterate   | O(n)
    memory    | O(n)
    """

    # Core operations #

    def __init__(self, mapping=None, **kwargs):
        self._keys = []
        self._vals = []
        self.update(mapping, **kwargs)

    def _lookup(self, key) -> (bool, int):
        """
        Lookup the given key.  Return whether it was found and, if so, its index.
        """
        for (idx, key_) in enumerate(self._keys):
            if key_ == key:
                return (True, idx)
        return (False, 0)

    def _insert(self, key, val) -> (bool, object):
        """
        Update the map to contain the given key-value pair.  Return whether
        the key already existed and, if so, its previous value.
        """
        found, idx = self._lookup(key)
        if found:
            old_val = self._vals[idx]
            self._vals[idx] = val
            return (True, old_val)
        else:
            self._keys.append(key)
            self._vals.append(val)
            return (False, None)

    def _delete(self, key) -> (bool, object):
        """
        Delete the given key and its value.  Return whether the key already
        existed and, if so, its previous value.
        """
        found, idx = self._lookup(key)
        if found:
            old_val = self._vals[idx]
            del self._keys[idx]
            del self._vals[idx]
            return (True, old_val)
        else:
            return (False, None)

    # Python dict API #

    ## Read ##

    def __len__(self):
        return len(self._keys)

    def __contains__(self, key):
        found, _ = self._lookup(key)
        return found

    def __getitem__(self, key):
        found, idx = self._lookup(key)
        if found:
            return self._vals[idx]
        else:
            raise KeyError(key)

    def get(self, key, default=None):
        found, idx = self._lookup(key)
        if found:
            return self._vals[idx]
        else:
            return default

    def __iter__(self):
        return self.keys()

    def keys(self):
        return iter(self._keys)

    def values(self):
        return iter(self._vals)

    def items(self):
        return zip(self._keys, self._vals)

    ## Write ##

    def __setitem__(self, key, value):
        self._insert(key, value)

    def update(self, mapping=None, **kwargs):
        if mapping is not None:
            for (key, val) in mapping:
                self.__setitem__(key, val)
        for (key, val) in kwargs.items():
            self.__setitem__(key, val)

    def __delitem__(self, key):
        found, _ = self._delete(key)
        if not found:
            raise KeyError(key)

    def clear(self):
        self._keys.clear()
        self._vals.clear()


class SortedPairsMap:
    """
    Map implemented as a sorted list of key-value pairs.

    Keys must be orderable.  Does not use hashing.  Follows the Python
    `dict` API.  Uses `==` for key equality, so beware of things like `0
    == False`.

    Operation | Complexity
    ======================
    lookup    | O(log n)
    insert    | O(n)
    delete    | O(n)
    length    | O(1)
    iterate   | O(n)
    memory    | O(n)
    """

    # Core operations #

    def __init__(self, mapping=None, **kwargs):
        self._keys = []
        self._vals = []
        self.update(mapping, **kwargs)

    def _lookup(self, key) -> (bool, int):
        """
        Lookup the given key.  Return whether it was found and, if so, its index.
        """
        idx = bisect.bisect_left(self._keys, key)
        return (idx < len(self._keys) and key == self._keys[idx], idx)

    def _insert(self, key, val) -> (bool, object):
        """
        Update the map to contain the given key-value pair.  Return whether
        the key already existed and, if so, its previous value.
        """
        found, idx = self._lookup(key)
        if found:
            old_val = self._vals[idx]
            self._vals[idx] = val
            return (True, old_val)
        else:
            self._keys.insert(idx, key)
            self._vals.insert(idx, val)
            return (False, None)

    def _delete(self, key) -> (bool, object):
        """
        Delete the given key and its value.  Return whether the key already
        existed and, if so, its previous value.
        """
        found, idx = self._lookup(key)
        if found:
            old_val = self._vals[idx]
            del self._keys[idx]
            del self._vals[idx]
            return (True, old_val)
        else:
            return (False, None)

    # Python dict API #

    ## Read ##

    def __len__(self):
        return len(self._keys)

    def __contains__(self, key):
        found, _ = self._lookup(key)
        return found

    def __getitem__(self, key):
        found, value = self._lookup(key)
        if found:
            return value
        else:
            raise KeyError(key)

    def get(self, key, default=None):
        found, value = self._lookup(key)
        if found:
            return value
        else:
            return default

    def __iter__(self):
        return self.keys()

    def keys(self):
        return iter(self._keys)

    def values(self):
        return iter(self._vals)

    def items(self):
        return zip(self._keys, self._vals)

    ## Write ##

    def __setitem__(self, key, value):
        self._insert(key, value)

    def update(self, mapping=None, **kwargs):
        if mapping is not None:
            for (key, val) in mapping:
                self.__setitem__(key, val)
        for (key, val) in kwargs.items():
            self.__setitem__(key, val)

    def __delitem__(self, key):
        found, _ = self._delete(key)
        if not found:
            raise KeyError(key)

    def clear(self):
        self._keys.clear()
        self._vals.clear()


class ArrayMap:
    """
    Map implemented as an array of possible key-value pairs.

    Keys must be integers in a contiguous range.  Good for small ranges
    or when the density of keys is high.  Does not use hashing.  Follows
    the Python `dict` API.

    Operation | Complexity
    ======================
    lookup    | O(1)
    insert    | O(1)
    delete    | O(1)
    length    | O(1)
    iterate   | O(key range size)
    memory    | O(key range size)
    """

    # Core operations #

    def __init__(self, size, key_lo=0, mapping=None, **kwargs):
        self._key_lo = key_lo
        self._key_hi = key_lo + size
        self._sentinel = object()
        self._vals = [self._sentinel] * size
        self._n_items = 0
        self.update(mapping, **kwargs)

    def _lookup(self, key) -> (bool, int):
        """
        Lookup the given key.  Return whether it was found and, if so, its index.
        """
        if self._key_lo <= key < self._key_hi:
            idx = key - self._key_lo
            return (self._vals[idx] is not self._sentinel, idx)
        else:
            return (False, 0)

    def _insert(self, key, val) -> (bool, object):
        """
        Update the map to contain the given key-value pair.  Return whether
        the key already existed and, if so, its previous value.
        """
        found, idx = self._lookup(key)
        if found:
            old_val = self._vals[idx]
            self._vals[idx] = val
            return (True, old_val)
        else:
            self._vals[idx] = val
            self._n_items += 1
            return (False, None)

    def _delete(self, key) -> (bool, object):
        """
        Delete the given key and its value.  Return whether the key already
        existed and, if so, its previous value.
        """
        found, idx = self._lookup(key)
        if found:
            old_val = self._vals[idx]
            self._vals[idx] = self._sentinel
            self._n_items -= 1
            return (True, old_val)
        else:
            return (False, None)

    # Python dict API #

    ## Read ##

    def __len__(self):
        return self._n_items

    def __contains__(self, key):
        found, _ = self._lookup(key)
        return found

    def __getitem__(self, key):
        found, value = self._lookup(key)
        if found:
            return value
        else:
            raise KeyError(key)

    def get(self, key, default=None):
        found, value = self._lookup(key)
        if found:
            return value
        else:
            return default

    def __iter__(self):
        return self.keys()

    def keys(self):
        return (self._key_lo + i for (i, v) in enumerate(self._vals)
                if v is not self._sentinel)

    def values(self):
        return (v for v in self._vals if v is not self._sentinel)

    def items(self):
        return ((self._key_lo + i, v) for (i, v) in enumerate(self._vals)
                if v is not self._sentinel)

    ## Write ##

    def __setitem__(self, key, value):
        self._insert(key, value)

    def update(self, mapping=None, **kwargs):
        if mapping is not None:
            for (key, val) in mapping:
                self.__setitem__(key, val)
        for (key, val) in kwargs.items():
            self.__setitem__(key, val)

    def __delitem__(self, key):
        found, _ = self._delete(key)
        if not found:
            raise KeyError(key)

    def clear(self):
        for idx in range(len(self._vals)):
            self._vals[idx] = self._sentinel
        self._n_items = 0


class CompactArrayMap: # TODO
    pass
