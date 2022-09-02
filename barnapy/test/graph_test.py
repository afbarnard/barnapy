#asdf


edge_types: undirected, directed, bidirected

is_undirected
is_directed
is_mixed
is_hypergraph

is_simple (vs. has multiple edges)
loops
has_loops
is_tree
is_connected
n_connected_components

support multiple different backing representations (adj list vs. adj matrix vs. DB)
copy into different representation

spanning trees:
min weight
max weight
random
maximally independent?


allow multiple edges?
allow loops?
allow edge types
allow hyper edges


data structures:
sorted arrays implemented as trees
tries
dense hash table (DB style)
(sparse) (multidimensional) bit arrays for adjacency tensors
(sparse) (multidimensional) arrays for weighted adjacency tensors


graph IO:
csv
yaml
adjacency matrix
issues are edge types, hypergraph edges


graph algorithms:
traversal (visits in various ways: DFS, BFS, BestFS, A*)
shortest path
all shortest paths
d-separation / graph separation
v-structures
topological equivalence classes
undirected dependence equivalent
random graphs
roots
cycle_rank
reverse edges
minimal pdag
labeled graph comparison
all cycles
all paths
relevant cycles
fundamental basis (for a given spanning tree)
minimum basis
chordal fill-in
clique finding
junction tree
