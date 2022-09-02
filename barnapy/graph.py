"""Basic graph implementation"""

# Copyright (c) 2017, 2022 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import collections


class Graph:

    # Construction and IO

    def __init__(
            self,
            node_store=None,
            edge_store=None,
            weight_store=None,
            default_weight=None,
            ):
        if node_store is None:
            self._node_store = DictSetNodeEdgeStore()
        if edge_store is None:
            if isinstance(self._node_store, DictSetNodeEdgeStore):
                self._edge_store = self._node_store
            else:
                self._edge_store = DictSetEdgeStore()
        if weight_store is None:
            self._weight_store = DictWeightStore()
        self._default_weight = default_weight

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

    def subgraph(self, nodes=None, edges=None):
        pass

    # Read-only query API

    def has_node(self, node):
        return self._node_store.has_node(node)

    def has_edge(self, node1, node2):
        return self._edge_store.has_edge(node1, node2)

    def has_path(self, nodes, closed=False):
        """
        Return whether the given sequence of nodes is a path in this graph.

        `nodes` is iterated at most once.
        """
        node_iter = iter(nodes)
        init_node = next(node_iter, None)
        if init_node is None:
            return True # Every graph contains the empty path
        if not self.has_node(init_node):
            return False
        prev_node = init_node
        next_node = next(node_iter, None)
        while next_node is not None:
            if not self.has_edge(prev_node, next_node):
                return False
            prev_node = next_node
            next_node = next(node_iter, None)
        if closed:
            return self.has_edge(prev_node, init_node)
        return True

    def has_cycle(self, nodes):
        return self.has_path(nodes, closed=True)

    def has_weight(self, node1, node2):
        return self._weight_store.has_weight(node1, node2)

    #def has_property(self): # TODO? how distinguish node properties from edge properties?

    def n_nodes(self):
        return self._node_store.n_nodes()

    def n_edges(self):
        return self._edge_store.n_edges()

    def nodes(self):
        return self._node_store.nodes()

    def edges(self):
        return self._edge_store.edges()

    def weight(self, node1, node2):
        return self._weight_store.weight(
            node1, node2, self._default_weight)

    def edges_weights(self):
        for edge in self.edges():
            yield (edge, self.weight(*edge))

    def out_degree(self, node):
        return self._edge_store.out_degree(node)

    def out_neighbors(self, node):
        return self._edge_store.out_neighbors(node)

    neighbors = out_neighbors

    def out_neighbors_weights(self, node):
        return (nbr, self.weight(node, nbr)) for nbr in self.out_neighbors(node)

    neighbors_weights = out_neighbors_weights

    def in_degree(self, node):
        return self._edge_store.in_degree(node)

    def in_neighbors(self, node):
        return self._edge_store.in_neighbors(node)

    def in_neighbors_weights(self, node):
        return (nbr, self.weight(nbr, node)) for nbr in self.in_neighbors(node)

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

    def set_weight(self, node1, node2, weight):
        # Add edge if it doesn't exist
        if not self.has_edge(node1, node2):
            self.add_edge(node1, node2)
        self._weight_store.set_weight(node1, node2, weight)

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(*edge)

    def add_path(self, nodes, closed=False):
        node_iter = iter(nodes)
        init_node = next(node_iter, None)
        if init_node is None:
            return
        prev_node = init_node
        next_node = next(node_iter, None)
        while next_node is not None:
            self.add_edge(prev_node, next_node)
            prev_node = next_node
        if closed:
            self.add_edge(prev_node, init_node)

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

    def del_weight(self, node1, node2):
        self._weight_store.del_weight(node1, node2)

    def del_nodes(self, nodes):
        for node in nodes:
            self.del_node(node)

    def del_edges(self, edges):
        for edge in edges:
            self.del_edge(edge)

    def del_path(self, nodes):
        for node in nodes:
            self.del_node(node)


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


class DictWeightStore:

    def __init__(self):
        self._edges_weights = {}

    def has_weight(self, node1, node2):
        return (node1, node2) in self._edges_weights

    def weight(self, node1, node2, default=None):
        return self._edges_weights.get((node1, node2), default)

    def set_weight(self, node1, node2, weight):
        self._edges_weights[node1, node2] = weight

    def del_weight(self, node1, node2):
        del self._edges_weights[node1, node2]


# Algorithms

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


def visit_depth_first(graph, start):
    pass


def visit(graph, start, min_wgt=None, max_wgt=None, first='breadth'):
    """assumes nonnegative weights"""
    pass


def shortest_path():
    pass


def shortest_paths_bds(graph, start, end, min_weight=None, max_weight=None):
    """"""
    # Path, nodes, queue for forward and reverse directions
    (p, n, q) = range(3)
    fwd_pnq = ([(start, 0)], {start: 0}, [(0, start, None)])
    rev_pnq = ([(end, 0)], {end: 0}, [(0, end, None)])
    # Start with the forward direction
    one_pnq = fwd_pnq
    oth_pnq = rev_pnq
    while len(one_pnq[q]) > 0:
        (dist, node, prev) = heapq.heappop(one_pnq[q])
        if node in oth_pnq[n]:
            yield
        nbrs_wgts = (graph.out_neighbors_weights(node)
                     if one_pnq is fwd_pnq
                     else graph.in_neighbors_weights(node))
        for (nbr, wgt) in nbrs_wgts:
            nbr_dist = dist + wgt
            if nbr_dist <= max_weight:
                heapq.heappush(one_pnq[q], (nbr_dist, nbr, node))


def all_cycles(graph):
    pass
