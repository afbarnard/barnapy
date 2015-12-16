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
                self._node_store.add(edge[0])
            elif len(edge) == 2:
                node1, node2 = edge
                self._node_store.add(node1)
                self._node_store.add(node2)
                self._edge_store.add(*edge)
            else:
                raise ValueError(
                    'Not interpretable as an edge: {}'.format(edge))

    def to_list_def(self):
        loners = set(self._node_store)
        for node1, node2 in self._edge_store:
            loners.discard(node1)
            loners.discard(node2)
            yield (node1, node2)
        for node in loners:
            yield (node,)

    def has_edge(self, node1, node2):
        return self._edge_store.has(node1, node2)

    def num_nodes(self):
        return len(self._node_store)

    def nodes(self):
        return iter(self._node_store)

    def num_edges(self):
        return len(self._edge_store)

    def edges(self):
        return iter(self._edge_store)


class SetNodeStore(set): # TODO subclass or wrap?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_node(self, node):
        self.add(node)

    def nodes(self):
        yield from iter(self)


class DictSetEdgeStore(dict): # TODO subclass or wrap?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        return iter(self.edges())

    def add(self, node1, node2):
        if node1 not in self:
            self[node1] = set()
        self[node1].add(node2)

    def has(self, node1, node2):
        if node1 in self:
            return node2 in self[node1]
        else:
            return False

    def edges(self):
        for node, neighbors in self.items():
            for neighbor in neighbors:
                yield (node, neighbor)
