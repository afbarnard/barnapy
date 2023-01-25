"""Tests `graph.py`."""

# Copyright (c) 2022-2023 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import itertools as itools
import string
import unittest

from .. import graph


test_graphs = {

    '3x3 grid S path': dict(
        draw=r'''
             1      1
          U------D------Y
        2 |    5 |    8 |
          |  1   |  2   |
          J------K------W
        9 |    6 |    1 |
          |  2   |  2   |
          S------M------P
        ''',
        dists={'UD': 1, 'DY': 1,
               'UJ': 2, 'DK': 5, 'YW': 8,
               'JK': 1, 'KW': 2,
               'JS': 9, 'KM': 6, 'WP': 1,
               'SM': 2, 'MP': 2},
    ),

    '4x6 grid random': dict(
        draw=r'''
             18      8      5     19      7
           W------T------M------P------G------Y
        14 |    6 |   10 |   16 |    9 |   14 |
           |  1   |  5   | 13   | 16   | 14   |
           E------X------U------L------K------A
        20 |   11 |   15 |   10 |    1 |    6 |
           |  2   |  9   |  7   | 11   | 17   |
           Q------B------N------J------S------F
         2 |   14 |   12 |    7 |    3 |    6 |
           | 11   | 12   |  8   |  6   | 10   |
           H------V------Z------D------C------R
        ''',
        dists={'WT': 18, 'TM':  8, 'MP':  5, 'PG': 19, 'GY':  7,
               'WE': 14, 'TX':  6, 'MU': 10, 'PL': 16, 'GK':  9, 'YA': 14,
               'EX':  1, 'XU':  5, 'UL': 13, 'LK': 16, 'KA': 14,
               'EQ': 20, 'XB': 11, 'UN': 15, 'LJ': 10, 'KS':  1, 'AF':  6,
               'QB':  2, 'BN':  9, 'NJ':  7, 'JS': 11, 'SF': 17,
               'QH':  2, 'BV': 14, 'NZ': 12, 'JD':  7, 'SC':  3, 'FR':  6,
               'HV': 11, 'VZ': 12, 'ZD':  8, 'DC':  6, 'CR': 10},
    ),

    'barbell': dict(
        draw=r'''
          A---B               C---D
         / \ / \             / \ / \
        E---*---F---G---H---I---*---J
         \ / \ /             \ / \ /
          K---L               M---N
        ''',
        edges=['AB', 'AE', 'AL', 'BF', 'BK', 'EF', 'EK', 'FL', 'KL',
               'FG', 'GH', 'HI',
               'CD', 'CI', 'CN', 'DJ', 'DM', 'IJ', 'IM', 'JN', 'MN'],
    ),

    'decreasing paths': dict(
        draw=r'''
          1   1   1   1   1   1   1   1
        A---B---C---D---E---F---G---H---I
        |17 |15 |13 |11 | 9 | 7 | 5 | 3 | 1
        `---`---`---`---`---`---`---`---K
        ''',
        dists={'AB': 1, 'AK': 17, 'BC': 1, 'BK': 15, 'CD': 1, 'CK': 13,
               'DE': 1, 'DK': 11, 'EF': 1, 'EK': 9, 'FG': 1, 'FK': 7,
               'GH': 1, 'GK': 5, 'HI': 1, 'HK': 3, 'IK': 1},
    ),

    'up down from A to Z': dict(
        draw=r'''
        ,---,---,---A---,---,---,
        | 1 | 3 | 5 | 7 | 9 |11 |13
        B   C   D   E   F   G   H
        |14 |13 |12 |11 |10 | 9 | 8
        `---`---`---Z---'---'---'
        ''',
        dists={'AB': 1, 'AC': 3, 'AD': 5, 'AE': 7, 'AF': 9, 'AG': 11, 'AH': 13,
               'BZ': 14, 'CZ': 13, 'DZ': 12, 'EZ': 11, 'FZ': 10, 'GZ': 9, 'HZ': 8},
    ),

    'random 1': dict(
        draw=r'''
              86    36           61
            O-----D-----E-----.-----K
                94|\90  |24    \2
              25  | \__ |  39   \___   34
            I-----M    'H-----Q.    Y-----F
           /       \8   |77 / | \41  \
          |   71    \__ | _/42|  \__  |
        82| A-----X----'P'----+-.   W |69
          |       |  19 |82   |  \61  |
           \  32  |9    N     |5  \_ /  16
            Z-----S     |33   T     U-----V
                  |19   G     |69   |82
                  |  90 |72   |     |
                  R-----O-----'-----'
        ''',
        nodes=string.ascii_uppercase,
        dists={'PQ': 42, 'MP':  8, 'QW': 41, 'SZ': 32, 'EK': 61, 'OU': 82,
               'HP': 77, 'RS': 19, 'HQ': 39, 'EY':  2, 'UV': 16, 'GN': 33,
               'DO': 86, 'AX': 71, 'UY': 69, 'DH': 90, 'OG': 72, 'DE': 36,
               'IZ': 82, 'NP': 82, 'IM': 25, 'QT':  5, 'FY': 34, 'PU': 61,
               'EH': 24, 'SX':  9, 'PX': 19, 'OT': 69, 'DM': 94, 'OR': 90},
    ),

    "Pascal's triangle": dict(
        draw=r'''
                    A1
                   / \
                  B1  C1
                 / \ / \
                D1  E2  F1
               / \ / \ / \
              G1  H3  I3  J1
             / \ / \ / \ / \
            K1  L4  M6  N4  O1
           / \ / \ / \ / \ / \
          P1  Q5  R10 S10 T5  U1
         / \ / \ / \ / \ / \ / \
        V1  W6  X15 Y20 Z15 a6  b1
        ''',
        # Distances are value at node below
        dists={'AB': 1, 'AC': 1,
               'BD': 1, 'BE': 2, 'CE': 2, 'CF': 1,
               'DG': 1, 'DH': 3, 'EH': 3, 'EI': 3, 'FI': 3, 'FJ': 1,
               'GK': 1, 'GL': 4, 'HL': 4, 'HM': 6, 'IM': 6, 'IN': 4, 'JN': 4, 'JO': 1,
               'KP': 1, 'KQ': 5, 'LQ': 5, 'LR': 10, 'MR': 10,
               'MS': 10, 'NS': 10, 'NT': 5, 'OT': 5, 'OU': 1,
               'PV': 1, 'PW': 6, 'QW': 6, 'QX': 15, 'RX': 15, 'RY': 20,
               'SY': 20, 'SZ': 15, 'TZ': 15, 'Ta': 6, 'Ua': 6, 'Ub': 1},
    ),

}


def mk_graph(grf_def):
    grf = graph.Graph(default_weight=1)
    if 'nodes' in grf_def:
        grf.add_nodes(grf_def['nodes'])
    for (node1, node2) in itools.chain(
            grf_def.get('edges', ()), grf_def.get('dists', {}).keys()):
        grf.add_edge(node1, node2)
        grf.add_edge(node2, node1)
    distf = None
    dists = grf_def.get('dists')
    if dists is not None:
        for ((n1, n2), wgt) in dists.items():
            grf.set_weight(n1, n2, wgt)
            grf.set_weight(n2, n1, wgt)
        distf = graph.Graph.weight
    return (grf, distf)


class ShortestPathTest(unittest.TestCase):

    def test_empty_graph(self):
        grf = graph.Graph()
        self.assertIsNone(graph.shortest_path(grf, 'A', 'B'))

    def test_no_edges(self):
        grf = graph.Graph()
        grf.add_nodes('ABC')
        self.assertIsNone(graph.shortest_path(grf, 'A', 'B'))

    def test_complete_graph(self):
        nodes = 'ABCDE'
        grf = graph.Graph()
        grf.add_nodes(nodes)
        grf.add_edges(itools.combinations(nodes, 2))
        grf.add_edges(itools.combinations(reversed(nodes), 2))
        for (node1, node2) in itools.chain(
                itools.combinations(nodes, 2),
                itools.combinations(reversed(nodes), 2)):
            self.assertEqual(([node1, node2], 1),
                             graph.shortest_path(grf, node1, node2))

    def test_plain_3x3_grid(self):
        shortest = {
            'UD': 1, 'UY': 2, 'UJ': 1, 'UK': 2, 'UW': 3, 'US': 2, 'UM': 3, 'UP': 4,
            'DY': 1, 'DJ': 2, 'DK': 1, 'DW': 2, 'DS': 3, 'DM': 2, 'DP': 3,
            'YJ': 3, 'YK': 2, 'YW': 1, 'YS': 4, 'YM': 3, 'YP': 2,
            'JK': 1, 'JW': 2, 'JS': 1, 'JM': 2, 'JP': 3,
            'KW': 1, 'KS': 2, 'KM': 1, 'KP': 2,
            'WS': 3, 'WM': 2, 'WP': 1,
            'SM': 1, 'SP': 2,
            'MP': 1,
        }
        (grf, _) = mk_graph(test_graphs['3x3 grid S path'])
        for ((node1, node2), dist_exp) in shortest.items():
            with self.subTest(f'{node1}{node2}'):
                (_, dist_act) = graph.shortest_path(grf, node1, node2)
                self.assertEqual(dist_exp, dist_act)

    def test_3x3_grid_S_path(self):
        shortest = {
            'UD': ('UD', 1), 'UY': ('UDY', 2), 'UJ': ('UJ', 2),
            'UK': ('UJK', 3), 'UW': ('UJKW', 5), 'US': ('UJKWPMS', 10),
            'UM': ('UJKWPM', 8), 'UP': ('UJKWP', 6),
            'DY': ('DY', 1), 'DJ': ('DUJ', 3), 'DK': ('DUJK', 4),
            'DW': ('DUJKW', 6), 'DS': ('DUJKWPMS', 11), 'DM': ('DUJKWPM', 9),
            'DP': ('DUJKWP', 7),
            'YJ': ('YDUJ', 4), 'YK': ('YDUJK', 5), 'YW': ('YDUJKW', 7),
            'YS': ('YDUJKWPMS', 12), 'YM': ('YDUJKWPM', 10),
            'YP': ('YDUJKWP', 8),
            'JK': ('JK', 1), 'JW': ('JKW', 3), 'JS': ('JKWPMS', 8),
            'JM': ('JKWPM', 6), 'JP': ('JKWP', 4),
            'KW': ('KW', 2), 'KS': ('KWPMS', 7), 'KM': ('KWPM', 5),
            'KP': ('KWP', 3),
            'WS': ('WPMS', 5), 'WM': ('WPM', 3), 'WP': ('WP', 1),
            'SM': ('SM', 2), 'SP': ('SMP', 4),
            'MP': ('MP', 2),
        }
        (grf, distf) = mk_graph(test_graphs['3x3 grid S path'])
        for ((node1, node2), (path_exp, dist_exp)) in shortest.items():
            with self.subTest(f'{node1}{node2}'):
                self.assertEqual((list(path_exp), dist_exp),
                                 graph.shortest_path(grf, node1, node2, distf))

    def test_barbell(self):
        shortest = {
            'LA': 1, 'AK': 2, 'EJ': 5, 'KD': 7,
            'JD': 1, 'ND': 2, 'MB': 5, 'NA': 7,
        }
        (grf, _) = mk_graph(test_graphs['barbell'])
        for ((node1, node2), dist_exp) in shortest.items():
            with self.subTest(f'{node1}{node2}'):
                (_, dist_act) = graph.shortest_path(grf, node1, node2)
                self.assertEqual(dist_exp, dist_act)

    def test_disconnected(self):
        (grf, _) = mk_graph(test_graphs['barbell'])
        grf.del_edge(*'GH')
        grf.del_edge(*'HG')
        for (node1, node2) in itools.product('ABEFKL', 'CDIJMN'):
            self.assertIsNone(graph.shortest_path(grf, node1, node2))
            self.assertIsNone(graph.shortest_path(grf, node2, node1))

    def test_decreasing_paths(self):
        (grf, distf) = mk_graph(test_graphs['decreasing paths'])
        self.assertEqual((list('ABCDEFGHIK'), 9),
                         graph.shortest_path(grf, 'A', 'K', distf))

    def test_up_down(self):
        (grf, distf) = mk_graph(test_graphs['up down from A to Z'])
        self.assertEqual((list('ABZ'), 15),
                         graph.shortest_path(grf, 'A', 'Z', distf))

    def test_excluded_nodes(self):
        (grf, distf) = mk_graph(test_graphs['3x3 grid S path'])
        for (beg, end, excl_nodes, exp) in [
                ('U', 'P', 'K', (list('UDYWP'), 11)),
                ('U', 'P', 'KY', (list('UJSMP'), 15)),
                ('U', 'P', 'SKY', None),
        ]:
            with self.subTest(f'from {beg} to {end} excluding {excl_nodes}'):
                self.assertEqual(exp, graph.shortest_path(
                    grf, beg, end, distf, excl_nodes))

    def test_excluded_edges(self):
        (grf, distf) = mk_graph(test_graphs['3x3 grid S path'])
        for (beg, end, excl_edges, exp) in [
                ('S', 'Y', 'SM', (list('SJUDY'), 13)),
                ('S', 'Y', 'SM DY', (list('SJKWY'), 20)),
                ('S', 'Y', 'SM JK DY KW', (list('SJUDKMPWY'), 34)),
                ('S', 'Y', 'DY KW MP', None),
        ]:
            excl_undir_edges = itools.chain.from_iterable(
                ((n1, n2), (n2, n1)) for (n1, n2) in excl_edges.split(' '))
            with self.subTest(f'from {beg} to {end} excluding {excl_edges}'):
                self.assertEqual(exp, graph.shortest_path(
                    grf, beg, end, distf, None, excl_undir_edges))

    def test_multiple_begins_ends(self):
        (grf, distf) = mk_graph(test_graphs['4x6 grid random'])
        for (begs, ends, excl, exp) in [
                ('WEQH', 'YAFR', '', (list('QBNJDCR'), 41)),
                ('WEQH', 'YAFR', 'D', (list('QBNJSCR'), 42)),
                ('WEQH', 'YAFR', 'DC', (list('QBNJSKA'), 44)),
                ('WEQH', 'YAFR', 'XBZPKS', (list('WTMUNJDCR'), 81)),
                ('WEQH', 'YAFR', 'PUBZ', None),
        ]:
            with self.subTest(f'from {begs} to {ends} excluding {excl}'):
                act = graph.shortest_path_btw_sets(
                    grf, begs, ends, distf, excl)
                self.assertEqual(exp, act)

    def test_is_distance_ok(self):
        (grf, distf) = mk_graph(test_graphs["Pascal's triangle"])
        # Minimum
        self.assertEqual((list('ABE'), 3), graph.shortest_path(
            grf, 'A', 'E', distf, is_distance_ok=lambda l: -1 if l < 3 else 0))
        self.assertEqual(None, graph.shortest_path(
            grf, 'A', 'E', distf, is_distance_ok=lambda l: -1 if l < 4 else 0))
        # Maximum
        self.assertEqual((list('ABDHM'), 11), graph.shortest_path(
            grf, 'A', 'M', distf, is_distance_ok=lambda l: 1 if l > 11 else 0))
        self.assertEqual(None, graph.shortest_path(
            grf, 'A', 'M', distf, is_distance_ok=lambda l: 1 if l > 10 else 0))
        # Range (only includes R and S)
        ilo = lambda l: -1 if l < 10 else (1 if l > 20 else 0)
        self.assertEqual((list('ACFJNS'), 17), graph.shortest_path(
            grf, 'A', 'S', distf, is_distance_ok=ilo))
        self.assertEqual(None, graph.shortest_path(
            grf, 'A', 'T', distf, is_distance_ok=ilo))
        self.assertEqual(None, graph.shortest_path(
            grf, 'A', 'X', distf, is_distance_ok=ilo))
