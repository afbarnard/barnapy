"""Basic graph implementation"""

# Copyright (c) 2017, 2022-2023 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import collections
import heapq
import warnings


class Graph:

    def __init__(
            self,
            node_store=None,
            edge_store=None,
            prop_store=True,
            weight_key='weight',
            default_weight=None,
    ):
        """
        Create a graph using the given data structures.

        A property store must be specified in order to use weights.

        `node_store`: NodeStore | None

            If `None`, a default node store will be created.

        `edge_store`: EdgeStore | None

            If `None`, the node store will be used if it also functions
            as an edge store.  Else a default edge store will be
            created.

        `prop_store`: PropertyStore | None | True

            If `None`, this graph will not support properties (and will
            use less memory).  If `True` then a default property store
            will be created.

        `weight_key`: hashable

            The key to use for the weight property.

        `default_weight`: object

            Value to use as the default weight.  If `None`, then the
            default weight is not set.
        """
        self._node_store = node_store
        self._edge_store = edge_store
        self._prop_store = prop_store
        if node_store is None:
            self._node_store = DictSetNodeEdgeStore()
        if edge_store is None:
            if isinstance(self._node_store, DictSetNodeEdgeStore):
                self._edge_store = self._node_store
            else:
                self._edge_store = DictSetEdgeStore()
        if prop_store is True:
            self._prop_store = DictPropertyStore()
        self.weight_key = weight_key
        if default_weight is not None:
            self.set_property_default(self.weight_key, default_weight)

    @staticmethod
    def from_nodes_edges(nodes_edges):
        _graph = Graph()
        for item in nodes_edges:
            if len(item) == 1 or (len(item) == 2 and item[1] is None):
                _graph.add_node(item[0])
            elif len(item) == 2:
                _graph.add_edge(*item)
            else:
                raise ValueError(
                    'Not interpretable as a node or edge: {}'
                    .format(item))
        return _graph

    # TODO `from_hyperedges`, `from_hyperedges_properties`

    def to_nodes_edges(self, sort=False):
        nodes = self.nodes()
        edges = self.edges()
        if sort:
            nodes = sorted(nodes)
            edges = sorted(edges)
        for node in nodes:
            yield (node,)
        for edge in edges:
            yield edge

    def to_nodes_edges_weights(self, sort=False):
        nodes = self.nodes()
        edges_weights = self.edges_weights()
        if sort:
            nodes = sorted(nodes)
            edges_weights = sorted(edges_weights)
        for node in nodes:
            yield (node,)
        for edge_weight in edges_weights:
            yield edge_weight

    # TODO `to_hyperedges`, `to_hyperedges_properties`

    # Properties

    @property
    def weight_key(self):
        return self._wgt_key

    @weight_key.setter
    def weight_key(self, key):
        self._wgt_key = key

    # Query API

    def has_node(self, node):
        return self._node_store.has_node(node)

    def has_edge(self, node1, node2):
        return self._edge_store.has_edge(node1, node2)

    def has_weight(self, node1, node2):
        return self.has_property(self.weight_key, node1, node2)

    def has_property(self, key, *nodes):
        if self._prop_store is None:
            return False
        return self._prop_store.has_property(key, *nodes)

    def has_property_default(self, key):
        if self._prop_store is None:
            return False
        return self._prop_store.has_property_default(key)

    def n_nodes(self):
        return self._node_store.n_nodes()

    def n_edges(self):
        return self._edge_store.n_edges()

    def out_degree(self, node):
        return self._edge_store.out_degree(node)

    def in_degree(self, node):
        return self._edge_store.in_degree(node)

    def nodes(self):
        return self._node_store.nodes()

    def edges(self):
        return self._edge_store.edges()

    def out_neighbors(self, node):
        return self._edge_store.out_neighbors(node)

    neighbors = out_neighbors

    def in_neighbors(self, node):
        return self._edge_store.in_neighbors(node)

    def weight(self, node1, node2, default=None):
        return self.property(self.weight_key, node1, node2,
                             value_if_not_exist=default)

    def property(self, key, *nodes, value_if_not_exist=None):
        return self._prop_store.get_property(
            key, *nodes, value_if_not_exist=value_if_not_exist)

    def property_default(key, value_if_not_exist=None):
        return self._prop_store.get_property_default(
            key, value_if_not_exist=value_if_not_exist)

    def edges_weights(self):
        for edge in self.edges():
            yield (edge, self.weight(*edge))

    nodes_properties = NotImplemented # TODO

    edges_properties = NotImplemented # TODO

    # Modification API

    def add_node(self, node):
        self._node_store.add_node(node)

    def add_edge(self, node1, node2, weight=None):
        self._node_store.add_node(node1)
        self._node_store.add_node(node2)
        self._edge_store.add_edge(node1, node2)
        # Only set a weight on the edge if specified
        if weight is not None:
            self.set_weight(node1, node2, weight)

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(*edge)

    def del_node(self, node):
        # Delete edges between this node and its neighbors
        for neighbor in list(self.in_neighbors(node)):
            self.del_edge(neighbor, node)
        for neighbor in list(self.out_neighbors(node)):
            self.del_edge(node, neighbor)
        # Then delete this node
        self._node_store.del_node(node)

    def del_edge(self, node1, node2):
        # Delete the weight, if any
        if self.has_weight(node1, node2):
            self.del_weight(node1, node2)
        self._edge_store.del_edge(node1, node2)

    def del_nodes(self, nodes):
        for node in nodes:
            self.del_node(node)

    def del_edges(self, edges):
        for edge in edges:
            self.del_edge(edge)

    def set_weight(self, node1, node2, weight):
        # Add edge if it doesn't exist
        if not self.has_edge(node1, node2):
            self.add_edge(node1, node2)
        self.set_property(self.weight_key, weight, node1, node2)

    def set_property(self, key, value, *nodes):
        self._prop_store.set_property(key, value, *nodes)

    def set_property_default(self, key, value):
        self._prop_store.set_property_default(key, value)

    def del_weight(self, node1, node2):
        self.del_property(self.weight_key, node1, node2)

    def del_property(self, key, *nodes):
        self._prop_store.del_property(key, *nodes)

    def del_property_default(self, key):
        self._prop_store.del_property_default(key)


class SetNodeStore:

    def __init__(self):
        self._nodes = set()

    def has_node(self, node):
        return node in self._nodes

    def n_nodes(self):
        return len(self._nodes)

    def nodes(self):
        return iter(self._nodes)

    def add_node(self, node):
        self._nodes.add(node)

    def del_node(self, node):
        self._nodes.remove(node)


class DictSetEdgeStore:

    def __init__(self):
        self._parents = {}

    def has_edge(self, node1, node2):
        return node1 in self._parents and node2 in self._parents[node1]

    def n_edges(self):
        return sum(len(children) for children in self._parents.values())

    def edges(self):
        for parent, children in self._parents.items():
            for child in children:
                yield (parent, child)

    def add_edge(self, node1, node2):
        children = self._parents.get(node1)
        if children is None:
            children = set()
            self._parents[node1] = children
        children.add(node2)

    def del_edge(self, node1, node2):
        self._parents[node1].remove(node2)

    def out_degree(self, node):
        if node in self._parents:
            return len(self._parents[node])
        else:
            return 0

    def in_degree(self, node):
        return sum(int(node in children)
                   for children in self._parents.values())

    def out_neighbors(self, node):
        if node in self._parents:
            return iter(self._parents[node])
        else:
            return iter(())

    def in_neighbors(self, node):
        return (parent for parent, children in self._parents.items()
                if node in children)


class DictSetNodeEdgeStore:

    def __init__(self):
        self._nodes2childrens = {}

    # Node API

    def has_node(self, node):
        return node in self._nodes2childrens

    def n_nodes(self):
        return len(self._nodes2childrens)

    def nodes(self):
        return self._nodes2childrens.keys()

    def add_node(self, node):
        # Only add the node if it hasn't already been added
        if node not in self._nodes2childrens:
            self._nodes2childrens[node] = set()

    def del_node(self, node):
        self._nodes2childrens.pop(node, None)

    # Edge API

    def has_edge(self, node1, node2):
        children = self._nodes2childrens.get(node1)
        if children is None:
            return False
        return node2 in children

    def n_edges(self):
        return sum(len(children) for children in self._nodes2childrens.values())

    def edges(self):
        for node, children in self._nodes2childrens.items():
            for child in children:
                yield (node, child)

    def add_edge(self, node1, node2):
        children = self._nodes2childrens.get(node1)
        if children is None:
            children = set()
            self._nodes2childrens[node1] = children
        children.add(node2)

    def del_edge(self, node1, node2):
        children = self._nodes2childrens.get(node1)
        if children is None:
            return
        children.discard(node2)

    def out_degree(self, node):
        return len(self._nodes2childrens[node])

    def in_degree(self, node):
        return sum(int(node in children)
                   for children in self._nodes2childrens.values())

    def out_neighbors(self, node):
        return iter(self._nodes2childrens[node])

    def in_neighbors(self, node):
        return (parent for (parent, children) in self._nodes2childrens.items()
                if node in children)


class DictPropertyStore:

    def __init__(self):
        # Store property values under the compound key (property_key,
        # *nodes) so that properties on nodes and arbitrary hyperedges
        # can be accommodated while being able to just pick off the
        # first item as the property key.  (The property key could be
        # last, but then one couldn't use the '*nodes' syntax.)  Store
        # default property values here too because that's more
        # memory-efficient than having a separate map.
        self._key_hedge2val = {}

    def has_property_default(self, property_key):
        return property_key in self._key_hedge2val

    def get_property_default(self, property_key, value_if_not_exist=None):
        return self._key_hedge2val.get(property_key, value_if_not_exist)

    def set_property_default(self, property_key, value):
        self._key_hedge2val[property_key] = value

    def del_property_default(self, property_key):
        if property_key in self._key_hedge2val:
            del self._key_hedge2val[property_key]

    def has_property(self, property_key, *nodes):
        return (property_key, *nodes) in self._key_hedge2val

    def get_property(self, property_key, *nodes, value_if_not_exist=None):
        """
        Return the stored property (if it exists), or return the
        default value (if it exists), or return the given value.
        """
        # Use a (hopefully) unique sentinel value
        value = self._key_hedge2val.get((property_key, *nodes), self)
        if value is self:
            value = self._key_hedge2val.get(property_key, value_if_not_exist)
        return value

    def set_property(self, property_key, value, *nodes):
        self._key_hedge2val[(property_key, *nodes)] = value

    def del_property(self, property_key, *nodes):
        key = (property_key, *nodes)
        if key in self._key_hedge2val:
            del self._key_hedge2val[key]


# Algorithms #


def visit_breadth_first(graph, start):
    """
    Generate all nodes reachable from the given node in breadth-first
    manner.
    """
    # Queue of unvisited nodes.  Seed with the neighbors of the start so
    # as not to yield the start unless it is reachable from itself.
    queue = collections.deque(graph.out_neighbors(start))
    # Visited nodes
    visited = set()
    # Search
    while queue:
        # Visit the next node if it hasn't already been visited
        node = queue.popleft()
        if node in visited:
            continue
        yield node
        visited.add(node)
        # Enqueue unvisited neighbors
        for neighbor in graph.out_neighbors(node):
            if neighbor not in visited:
                queue.append(neighbor)


def path_exists_bfs(graph, start, end):
    """
    Whether a path from start to end exists in the given graph.

    Uses breadth-first search.
    """
    for node in visit_breadth_first(graph, start):
        if node == end:
            return True
    return False


## Shortest Paths ##


def _check_excluded_nodes(nodes_label, nodes, excluded_nodes):
    n_excluded = len(nodes & excluded_nodes)
    if n_excluded == len(nodes):
        raise ValueError(f'All {nodes_label} nodes are excluded')
    elif n_excluded > 0:
        warnings.warn(f'Some {nodes_label} nodes are excluded')


def shortest_path_btw_sets(
        graph,
        begins,
        ends,
        distance=None,
        excluded_nodes=None,
        excluded_edges=None,
        is_distance_ok=None,
):
    """
    Find a shortest path in a graph between the given sets of begin
    nodes and end nodes.  Return the path as `([begin, ..., end], total
    distance)` or `None` if no path exists.

    This is an implementation of Dijkstra's algorithm that generalizes
    it as much as possible without changing its structure or complexity.
    As such, this operates by expanding a shortest paths spanning tree
    until one of the goal nodes is found.  If the distance to that node
    is OK according to `is_distance_ok`, then it is returned.  Else the
    search continues.  This means that a node will only be returned if
    its shortest path is OK; a longer path to that node will not be
    considered, even if it might satisfy `is_distance_ok`.

    Note that Dijkstra's algorithm does not work for finding a shortest
    path from X to X (a shortest cycle) because that requires a
    fundamentally different search.  However, one can find a shortest
    cycle from X to X through neighbor Y by finding a shortest path from
    X to Y when excluding edge X-Y.

    `begins`: iterable[node]

        Collection of nodes to begin with.

    `ends`: iterable[node]

        Collection of nodes to end with.

    `distance`: callable(graph, node1, node2) -> distance >= 0 | None

        Function to give the distance along each edge.  If `None`, the
        distance / length / weight of each edge is 1.

    `excluded_nodes`: iterable[node] | None

        Nodes to exclude from all paths.  Pretends the subgraph induced
        by these nodes does not exist.

    `excluded_edges`: iterable[(node, node)] | None

        Edges to exclude from all paths.  Pretends the given edges do
        not exist.

    `is_distance_ok`: callable(distance) -> {-1, 0, 1} | None

        Function that decides whether a given path length (total
        distance) is too short (return -1), too long (+1), or is
        acceptable (0).  If `None`, every path length is acceptable, and
        so the first (and necessarily shortest) path found will be
        returned.

        If this function returns 1, then the search terminates
        immediately because the current shortest path is already too
        long.  This is useful for pruning the search.  Otherwise, the
        return value of this function is considered only if a goal node
        is found.
    """
    # Collect iterable arguments.  Filter out nodes not in the graph.
    begs = [beg for beg in begins if graph.has_node(beg)]
    ends = set(end for end in ends if graph.has_node(end))
    # Treat no nodes and nodes not in the graph as having no path
    if len(begs) == 0 or len(ends) == 0:
        return None
    # The shortest paths spanning tree.  Visted nodes are mapped to
    # their distance and parent in the SPST.  Seed it with the excluded
    # nodes to exclude them from the search.
    spst = ({}
            if excluded_nodes is None
            else {node: None for node in excluded_nodes})
    # Finish setting up the exclusions.  Check them for sanity.
    excl_edges = (set(tuple(e) for e in excluded_edges)
                  if excluded_edges is not None else None)
    _check_excluded_nodes('begin', begs, spst.keys())
    _check_excluded_nodes('end', ends, spst.keys())
    # Create a min priority queue for the shortest paths reached so far
    queue = [(0, node, None) for node in begs]
    # Search for an end
    while len(queue) > 0:
        # Get the node with the smallest total distance
        (dist_node, node, prev) = heapq.heappop(queue)
        # Check whether the current distance is acceptable.  Terminate
        # the search immediately if the distance is already too long.
        len_cmp = (is_distance_ok(dist_node)
                   if is_distance_ok is not None
                   else 0)
        if len_cmp >= 1:
            return None
        # If this node has already been visited, then continue, because
        # a shorter distance to it was already found
        if node in spst:
            continue
        # This is the shortest path to this node, so add it to the SPST
        spst[node] = (dist_node, prev)
        # If a suitable end was found, return the path
        if node in ends and len_cmp == 0:
            rev_path = [node]
            while prev is not None:
                rev_path.append(prev)
                (_, prev) = spst[prev]
            return (list(reversed(rev_path)), dist_node)
        # Explore neighbors for new or shorter paths
        for nbr in graph.out_neighbors(node):
            # Only process neighbors not visited or excluded
            if nbr not in spst and (excl_edges is None or
                                    (node, nbr) not in excl_edges):
                # Find the distance to the neighbor
                dist_edge = (1
                             if distance is None
                             else distance(graph, node, nbr))
                dist_nbr = dist_node + dist_edge
                # Enqueue this neighbor
                heapq.heappush(queue, (dist_nbr, nbr, node))
    # No path found
    return None


def shortest_path(graph, begin, end, *args, **kwds):
    """
    Call `shortest_path_btw_sets(graph, (begin,), (end,), *args,
    **kwds)`.
    """
    return shortest_path_btw_sets(graph, (begin,), (end,), *args, **kwds)


# TODO generator for all shortest paths that can handle tied lengths
# TODO generator for all simple paths
# TODO undirected graphs (undirected vs. directed has to do with storage and neighbors, not edge types)
# TODO how enforce correspondence between hyperedges and properties?
# TODO self edges? (n_self_edges)
# TODO multiple edges? (n_multi_edges) n_edges - n_self_edges - n_multi_edges -> n_simple_edges (graph is simple if `n_self_edges == 0 and n_multi_edges == 0`)
# TODO fully support hyperedges
