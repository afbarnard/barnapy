"""Trees and tries."""

# Copyright (c) 2021 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


class IndexableKey:
    pass


class RadixTree:
    """
    Radix tree (compact trie) implementation of `dict` API.  Radix trees
    map indexable keys to values without hashing.
    """

    # Analysis
    #
    # There are several ways a lookup key can compare against a stored
    # key.  This analysis breaks them down and establishes the
    # properties necessary for implementation.  The following
    # illustration demonstrates the various comparisons, where R is the
    # root, K indicates a split node (as if there was a key, but there
    # is no stored value), V indicates a node with a value (the end of a
    # stored key), and O indicates the end of a lookup key.
    #
    #       O---V         lookup key is a prefix of a stored key
    #      /
    # R---KO----VO---VO   matches at internal and leaf nodes
    #  .   \  `....O      lookup and stored keys have common prefix
    #   .   V...O         lookup key extends stored key
    #    O                lookup key entirely unique (extends root)
    #
    # * node depth: position in key where node is (root is zero)
    # * difference depth: position in lookup and stored keys where first
    #   difference between them occurs
    #
    # * lookup key matches stored key (up to some node)
    #   * key in map? yes, if node has a value, otherwise no
    #   * node depth == difference depth == key length
    #   * location is a node and node may or may not have children
    #   * insert: just update value
    # * lookup key extends stored key (or root) (divergence at a node)
    #   * key in map? no
    #   * node depth == difference depth <= lookup key length
    #   * location is a node and node may or may not have children
    #   * insert: create list of children if at leaf, add child
    # * lookup key is a prefix of a stored key (match ends between
    #   nodes)
    #   * key in map? no
    #   * node depth < difference depth == lookup key length
    #   * location is between nodes and previous node has children
    #   * insert: add split node
    # * common prefix (divergence between nodes)
    #   * key in map? no
    #   * node depth < difference depth
    #   * location is between nodes and previous node has children
    #   * insert: add split node, add child
    #
    #
    # Data Structure Implementation
    #
    # Each node in the tree is a mapping of objects at key[index] (for a
    # particular index) to entries describing the values and children.
    # An entry is a (rest of current key prefix, value, children) tuple.
    # If the rest of the key is not empty, then it is treated as part of
    # the key up to this point.  This allows for arbitrarily long
    # prefixes to be shared between keys (which is the crucial property
    # for space savings in radix trees).  If `value` is not the sentinel
    # value, then this mapping contains the key, and the key is mapped
    # to `value`.  If `children` is not None, then there exist children
    # with values mapped from extensions of the current key prefix.

    # Core operations

    def __init__(self, mapping=None, **kwargs):
        """
        Constructs an empty tree and calls `update` to populate it with the
        given key-value pairs.

        This implementation naïvely use `dict`s for nodes for the time
        being.
        """
        # Create a unique sentinel value
        self._sentinel = object()
        # Construct an empty tree
        self._n_items = 0
        self._root = {} # TODO replace with a non-hashing associative array
        self._empty_key = None
        self._empty_key_value = self._sentinel
        # Add the given key-value pairs
        self.update(mapping, **kwargs)

    def _lookup(self, key) -> (
            bool, object, dict, object, tuple, int, int, int):
        """
        Look up the key and return a tuple describing the situation.

        Tuple items:

        * found: whether the given key exists in the tree

        * value: the value the given key maps to, if any; if the key is
          not found, this is `None`

        * node: node that does / would contain the sought key-value
          pair; node to insert into (may be None in the case that a
          lookup key extends a stored key); a node is a mapping of
          key[i] to entries describing keys, values, and children

        * node key: key[i], the element of the given key that is the key
          for the mapping in the returned node; it may or may not exist
          in the node (which is described by `found`)

        * entry: (key extension, value, child node) tuple

        * node index: index in key at which the returned node starts,
          the i in key[i] above

        * diff index: index in key of the first difference between the
          lookup key and the stored key, the index at which they start
          to branch

        Invariant: node index <= diff index.
        """
        path = []
        node = self._root
        # The key index tracks how much of the lookup key has been
        # matched
        node_idx = 0
        key_idx = 0
        key_len = len(key)
        # Loop to look up the given key
        while node is not None and key_idx < key_len:
            # Index in the key at which this node starts
            node_idx = key_idx
            # Look for the key in the current node (which is a mapping)
            node_key = key[key_idx]
            entry = node.get(node_key)
            # Push this node onto the path
            path.append((node, node_key, entry))
            # Divergence at a node
            if entry is None:
                return (False, None, path, node_idx, key_idx)
            # Continue looking for the key in the current entry by
            # comparing it to the stored key extension
            key_ext, value, children = entry
            key_idx += 1
            key_ext_idx = 0
            key_ext_len = len(key_ext)
            while key_ext_idx < key_ext_len:
                # Divergence between nodes
                if ((key_idx + key_ext_idx) >= key_len
                        or key[key_idx + key_ext_idx] != key_ext[key_ext_idx]):
                    return (False, None, path, node_idx, key_idx + key_ext_idx)
                key_ext_idx += 1
            # At this point, the lookup key matches a stored key up to
            # some node so increment and "recurse"
            key_idx += key_ext_len
            node = children
        if key_idx == key_len:
            # Handle empty keys specially
            if key_len == 0:
                value = self._empty_key_value
                path.append((None, None, None))
            # No divergence.  This is a key match if the value is not
            # the sentinel value.
            return (value is not self._sentinel, value, path, key_idx, key_idx)
        elif node is None:
            # Lookup key extends a stored key
            assert key_idx < key_len
            path.append((None, None, None))
            return (False, None, path, key_idx, key_idx)
        else:
            raise AssertionError(
                f'Assertion `key_idx <= key_len` failed: {key_idx} <= {key_len}')

    def _insert(self, key, value) -> (bool, object):
        """
        Insert the given key-value pair, overwriting any existing value.

        Return whether the key previously existed and its previous value
        (or `None`, if it did not previously exist).
        """
        found, old_value, path, node_idx, diff_idx = self._lookup(key)
        assert node_idx <= diff_idx <= len(key)
        node, node_key, entry = path[-1]
        # Insert at a node
        if node_idx == diff_idx:
            # Key match, entry exists
            if diff_idx == len(key):
                if diff_idx == 0:
                    self._empty_key = key
                    self._empty_key_value = value
                else:
                    key_ext, _, children = entry
                    node[node_key] = (key_ext, value, children)
                # Do not leak the sentinel value
                if found:
                    return (True, old_value)
                else:
                    self._n_items += 1
                    return (False, None)
            else:
                # Lookup key and stored key share a common prefix.
                # Lookup key may extend stored key.
                insert_key = key[diff_idx]
                insert_entry = (key[(diff_idx + 1):], value, None)
                if node is None:
                    # Lookup key extends stored key so node is a leaf.
                    # Create new children.
                    parent_node, node_key, entry = path[-2]
                    key_ext, value, children = entry
                    assert children is None
                    node = {}
                    parent_node[node_key] = (key_ext, value, node)
                node[insert_key] = insert_entry
                self._n_items += 1
                return (False, None)
        # Insert between nodes
        else:
            # All found keys must hit the other branch
            assert found is False
            # Split the stored key
            key_ext, stored_value, childs_children = entry
            ext_diff_idx = diff_idx - (node_idx + 1)
            new_ext_prefix = key_ext[:ext_diff_idx]
            new_ext_suffix = key_ext[(ext_diff_idx + 1):]
            # Create a new child to take over this node's children
            children = {}
            children[key_ext[ext_diff_idx]] = (
                new_ext_suffix, stored_value, childs_children)
            # Does the new key just share a common prefix (and has its
            # own suffix) or is it a prefix of the stored key?
            if diff_idx < len(key):
                children[key[diff_idx]] = (key[(diff_idx + 1):], value, None)
                new_parent_value = self._sentinel
            else:
                new_parent_value = value
            # Hook the new children into the existing parent node
            node[node_key] = (new_ext_prefix, new_parent_value, children)
            self._n_items += 1
            return (False, None)

    def _delete(self, key) -> (bool, object):
        """
        Delete the given key and its associated value if they exist.

        Return whether the key previously existed and its previous value
        (or `None`, if it did not previously exist).
        """
        found, old_value, node, node_key, entry, *_ = self._lookup(key)
        if not found:
            return (False, None)
        key_ext, value, child_node = entry
        # Just remove the value for now # TODO remove tree structure that's no longer necessary
        node[node_key] = (key_ext, self._sentinel, child_node)
        self._n_items -= 1
        return (True, value) # Your favorite neighborhood hardware store?

    def _visit_items(self, sort=False):
        if self._empty_key_value is not self._sentinel:
            yield (self._empty_key, self._empty_key_value)
        kv_pairs = self._root.items()
        if sort:
            kv_pairs = sorted(kv_pairs, key=lambda kv: (kv[0], kv[1][0]))
        node_stack = [iter(kv_pairs)]
        key_stack = []
        while len(node_stack) > 0:
            next_item = next(node_stack[-1], None)
            if next_item is None:
                del node_stack[-1]
                if len(key_stack) > 0:
                    del key_stack[-1]
                continue
            (key_piece, (key_ext, value, children)) = next_item
            if len(key_stack) > 0:
                key = key_stack[-1] + key_piece + key_ext
            else:
                key = key_piece + key_ext
            if value is not self._sentinel:
                yield (key, value)
            if children:
                kv_pairs = children.items()
                if sort:
                    kv_pairs = sorted(
                        kv_pairs, key=lambda kv: (kv[0], kv[1][0]))
                node_stack.append(iter(kv_pairs))
                key_stack.append(key)

    # Read

    def __len__(self):
        return self._n_items

    def __contains__(self, key):
        found, *_ = self._lookup(key)
        return found

    def __getitem__(self, key):
        found, value, *_ = self._lookup(key)
        if found:
            return value
        else:
            raise KeyError(key)

    def get(self, key, default=None):
        found, value, *_ = self._lookup(key)
        if found:
            return value
        else:
            return default

    def __iter__(self):
        return self.keys()

    def keys(self):
        for (key, _) in self._visit_items():
            yield key

    def values(self):
        for (_, value) in self._visit_items():
            yield value

    def items(self, sort=False):
        return self._visit_items(sort=sort)

    # Write

    def __setitem__(self, key, value):
        self._insert(key, value)

    def update(self, mapping=None, **kwargs):
        if mapping is not None:
            for (key, value) in mapping:
                self.__setitem__(key, value)
        for (key, value) in kwargs.items():
            self.__setitem__(key, value)

    def __delitem__(self, key):
        found, *_ = self._delete(key)
        if not found:
            raise KeyError(key)

    def clear(self):
        self.__init__()
