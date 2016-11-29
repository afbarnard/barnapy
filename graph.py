"""Basic graph implementation

Copyright (c) 2016 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.
"""


class Graph:

    def __init__(
            self,
            node_store=None,
            edge_store=None,
            weight_store=None,
            default_weight=None,
            ):
        self._node_store = (node_store
                            if node_store is not None
                            else SetNodeStore())
        self._edge_store = (edge_store
                            if edge_store is not None
                            else DictSetEdgeStore())
        self._weight_store = (weight_store
                              if weight_store is not None
                              else DictWeightStore())
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

    def has_node(self, node):
        return self._node_store.has_node(node)

    def has_edge(self, node1, node2):
        return self._edge_store.has_edge(node1, node2)

    def has_weight(self, node1, node2):
        return self._weight_store.has_weight(node1, node2)

    def number_nodes(self):
        return self._node_store.number_nodes()

    def number_edges(self):
        return self._edge_store.number_edges()

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

    def del_node(self, node):
        # Delete edges between this node and its neighbors
        for neighbor in self.in_neighbors(node):
            self.del_edge(neighbor, node)
        for neighbor in self.out_neighbors(node):
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

    def out_degree(self, node):
        return self._edge_store.out_degree(node)

    def in_degree(self, node):
        return self._edge_store.in_degree(node)

    def out_neighbors(self, node):
        return self._edge_store.out_neighbors(node)

    def in_neighbors(self, node):
        return self._edge_store.in_neighbors(node)


class SetNodeStore:

    def __init__(self):
        self._nodes = set()

    def has_node(self, node):
        return node in self._nodes

    def number_nodes(self):
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

    def number_edges(self):
        return sum(len(children) for children in self._parents.values())

    def edges(self):
        for parent, children in self._parents.items():
            for child in children:
                yield (parent, child)

    def add_edge(self, node1, node2):
        if node1 not in self._parents:
            self._parents[node1] = set()
        self._parents[node1].add(node2)

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
