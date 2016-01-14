# Basic graph implementation

class Graph:

    def __init__(self, node_store=None, edge_store=None):
        self._node_store = (node_store
                            if node_store is not None
                            else SetNodeStore())
        self._edge_store = (edge_store
                            if edge_store is not None
                            else DictSetEdgeStore())

    def from_list_def(self, edges):
        for edge in edges:
            if len(edge) == 1 or (len(edge) == 2 and edge[1] is None):
                self.add_node(edge[0])
            elif len(edge) == 2:
                self.add_edge(*edge)
            else:
                raise ValueError(
                    'Not interpretable as an edge: {}'.format(edge))

    def to_list_def(self):
        loners = set(self._node_store.nodes())
        for node1, node2 in self._edge_store.edges():
            loners.discard(node1)
            loners.discard(node2)
            yield (node1, node2)
        for node in loners:
            yield (node,)

    def has_node(self, node):
        return self._node_store.has_node(node)

    def has_edge(self, node1, node2):
        return self._edge_store.has_edge(node1, node2)

    def number_nodes(self):
        return self._node_store.number_nodes()

    def number_edges(self):
        return self._edge_store.number_edges()

    def nodes(self):
        return self._node_store.nodes()

    def edges(self):
        return self._edge_store.edges()

    def add_node(self, node):
        self._node_store.add_node(node)

    def add_edge(self, node1, node2):
        self._node_store.add_node(node1)
        self._node_store.add_node(node2)
        self._edge_store.add_edge(node1, node2)

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_edges(self, edges):
        for node1, node2 in edges:
            self.add_edge(node1, node2)

    def out_degree(self, node):
        return self._edge_store.out_degree(node)

    def in_degree(self, node):
        return self._edge_store.in_degree(node)


class SetNodeStore():

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


class DictSetEdgeStore():

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

    def out_degree(self, node):
        if node in self._parents:
            return len(self._parents[node])
        else:
            return 0

    def in_degree(self, node):
        return sum(int(node in children)
                   for children in self._parents.values())
