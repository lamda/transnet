# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals
import unittest
import networkx as nx
import operator
from main import Node, Network


class TestGraph(unittest.TestCase):
    def test_travel_time_simple(self):
        graph = nx.DiGraph()
        A = Node(0, 0, 0, 'A', 1)
        B = Node(0, 0, 0, 'B', 1)
        C = Node(0, 0, 0, 'C', 1)

        Y = Node(0, 0, 0, 'Y', 1)
        Z = Node(0, 0, 0, 'Z', 1)

        graph.add_edge(A, B, {'weight': 1})
        graph.add_edge(B, A, {'weight': 1})
        graph.add_edge(B, C, {'weight': 1})
        graph.add_edge(C, B, {'weight': 1})

        graph.add_edge(Y, B, {'weight': 1})
        graph.add_edge(B, Y, {'weight': 1})
        graph.add_edge(Z, B, {'weight': 1})
        graph.add_edge(B, Z, {'weight': 1})
        n = Network(None)
        tt = n.travel_time(graph)
        for n in sorted(tt.iteritems(), key=operator.itemgetter(1)):
            print '%.3f' % n[1], n[0].name
        print '-----------------------------------------'


def test_all():
    t = TestGraph('test_travel_time_simple')
    t.test_travel_time_simple()


if __name__ == '__main__':
    test_all()