"""
Registering objects with keys.  Good for mapping names to objects in
APIs.
"""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


from collections.abc import Callable, Hashable, Iterable


class RegistryError(Exception):
    pass


class Entry:
    """
    Abstract superclass of registry entries.

    The value of an entry is computed (derived) by combining the value
    of its parent with its partial value.
    """

    def __repr__(self) -> str:
        """
        Assemble and return a string representation of this registry
        entry.
        """
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(f'{k.lstrip("_")}={v!r}'
                      for (k, v) in self.__dict__.items()))

    def parent_key(self) -> Hashable | None:
        """Return the key of the parent of this registry entry, if any."""
        return None

    def value(self, registry) -> object:
        """
        Return the value of this registry entry, deriving it as
        necessary from parent values.
        """
        raise NotImplementedError('Abstract method')

    def partial_value(self, registry) -> object:
        """Return the partial value of this registry entry."""
        raise NotImplementedError('Abstract method')

    def set_partial_value(self, registry, value: object):
        """Set this registry entry's partial value to the given value."""
        raise NotImplementedError('Abstract method')


class AliasEntry(Entry):
    """Registry entry that just aliases another registry entry."""

    def __init__(self, parent_key):
        self._parent_key = parent_key

    def parent_key(self):
        return self._parent_key

    def value(self, registry):
        return registry.value(self.parent_key())

    def partial_value(self, registry):
        return registry.entry(self.parent_key()).partial_value(registry)

    def set_partial_value(self, registry, value):
        registry.entry(self.parent_key()).set_partial_value(registry, value)


class RootEntry(Entry):
    """
    Registry entry with no parent, and so whose partial value and
    derived value are the same.
    """

    def __init__(self, value):
        self._value = value

    def value(self, registry):
        return self._value

    partial_value = value

    def set_partial_value(self, registry, value):
        self._value = value


class DerivedValueEntry(Entry):
    """
    Registry entry whose value is derived from the value of its
    parent.
    """

    def __init__(
            self,
            parent_key: Hashable,
            partial_value: object,
            deriver: Callable[[object, object], object],
    ):
        self._parent_key = parent_key
        self._partial_value = partial_value
        self._deriver = deriver

    def parent_key(self):
        return self._parent_key

    def value(self, registry):
        parent_value = registry.value(self.parent_key())
        return self._deriver(parent_value, self._partial_value)

    def partial_value(self, registry):
        return self._partial_value

    def set_partial_value(self, registry, value):
        self._partial_value = value

    @staticmethod
    def override_value(base: object, override: object) -> object:
        return override

    @staticmethod
    def overlay_dict(
            base: dict,
            overlay: dict | Iterable[tuple[Hashable, object]],
            **kwargs,
    ) -> dict:
        overlayed = dict(base)
        overlayed.update(overlay, **kwargs)
        return overlayed

    @classmethod
    def Overrider(clas, parent_key: Hashable, value: object):
        return clas(parent_key, value, DerivedValueEntry.override_value)

    @classmethod
    def Overlayer(clas, parent_key: Hashable, value: dict):
        return clas(parent_key, value, DerivedValueEntry.overlay_dict)


class DynamicEntry(DerivedValueEntry):
    """
    Registry entry whose value is always recomputed from the value
    of its parent.
    """


class StaticEntry(DynamicEntry):
    """Registry entry whose value is only computed once and then saved."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = None

    def value(self, registry):
        if self._value is None:
            self._value = super().value(registry)
        return self._value

    def set_partial_value(self, registry, value):
        super().set_partial_value(registry, value)
        self._value = None


class HierarchicalRegistry:
    """
    Register values with keys where values can derive from other
    values.

    Also acts like a read-only 'dict' that maps keys to values.  (The
    registry entries are not exposed.)  However, note that values may be
    (re)computed on each lookup and that each lookup may involve
    traversing the hierarchy, so lookup should not be considered
    constant time.
    """

    def __init__(self, name: str):
        """Create a hierarchical registry named with the given name."""
        self._name = name
        self._reg = dict()

    def n_entries(self) -> int:
        """Return how many entries this registry contains."""
        return len(self._reg)

    def has_key(self, key: Hashable) -> bool:
        """Whether this registry has the given key."""
        return key in self._reg

    def entry(self, key: Hashable) -> Entry:
        """Return the entry registered with the given key."""
        return self._reg[key]

    def parent_key(self, key: Hashable) -> Hashable | None:
        """Return the parent key of the given key, if any."""
        return self.entry(key).parent_key()

    def path(self, key: Hashable) -> list:
        """
        Return the "path" of the given key.

        Like a filesystem path, the path is the list of keys that lead
        to the given key from its root.
        """
        keys = []
        while key is not None:
            parent = self.parent_key(key)
            keys.append(key)
            key = parent
        keys.reverse()
        return keys

    def value(self, key: Hashable) -> object:
        """
        Compute and return the value registered with the given key.

        Note that computing the value may involve looking up each parent
        and computing their value recursively until the root.
        """
        return self.entry(key).value(self)

    def register(self, key: Hashable, entry: Entry):
        """
        Register the given entry with the given key.

        The key must not be 'None', must not already be registered, and
        the parent of the entry must already exist in the registry (or
        be 'None' in which case it's a root).
        """
        if key is None:
            raise RegistryError("'None' is not allowed as a registry key")
        if key in self._reg:
            raise RegistryError(f'Key already registered: {key!r}')
        parent = entry.parent_key()
        if parent is not None and parent not in self._reg:
            raise RegistryError(
                f'Parent of key {key!r} does not exist: {parent!r}')
        self._reg[key] = entry
        return self

    def register_all(self, keys_entries: Iterable[tuple[Hashable, Entry]]):
        for (key, entry) in keys_entries:
            self.register(key, entry)
        return self

    def __repr__(self) -> str:
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__, self._name, self._reg)

    # Partial (read-only) 'dict' interface

    __len__ = n_entries

    def __iter__(self):
        """Return an iterator over this registry's keys."""
        return iter(self._reg)

    __contains__ = has_key

    __getitem__ = value

    def get(self, key: Hashable, default: object=None) -> object:
        """
        Get the value for the given key if it is registered else
        return 'default'.
        """
        return self.value(key) if self.has_key(key) else default

    def keys(self):
        """Return a set-like view of this registry's keys."""
        return self._reg.keys()

    def values(self):
        """
        Return an iterator over values, recomputing them as
        necessary.
        """
        return (self.value(k) for k in self.keys())

    def items(self):
        """
        Return an iterator over (key, value) pairs, recomputing
        values as necessary.
        """
        return ((k, self.value(k)) for k in self.keys())
