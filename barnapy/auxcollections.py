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
