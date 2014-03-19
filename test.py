# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals
import unittest
import networkx as nx
import operator
from main import Network


class TestGraph(unittest.TestCase):
    def test_travel_time(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', {'weight': 1})
        graph.add_edge('B', 'A', {'weight': 1})
        graph.add_edge('B', 'C', {'weight': 1})
        graph.add_edge('C', 'B', {'weight': 1})

        graph.add_edge('1', 'B', {'weight': 1})
        graph.add_edge('B', '1', {'weight': 1})
        graph.add_edge('3', 'B', {'weight': 1})
        graph.add_edge('B', '3', {'weight': 1})
        n = Network(None)
        tt = n.travel_time(graph)
        for n in sorted(tt.iteritems(), key=operator.itemgetter(1)):
            print '%.3f' % n[1], n[0]
        print '-----------------------------------------'

    def test_travel_time_2(self):
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', {'weight': 1})
        graph.add_edge('B', 'A', {'weight': 1})
        graph.add_edge('B', 'C', {'weight': 1})
        graph.add_edge('C', 'B', {'weight': 1})

        graph.add_edge('B', 'D', {'weight': 1})
        graph.add_edge('D', 'B', {'weight': 1})

        graph.add_edge('D', 'C', {'weight': 5})
        graph.add_edge('C', 'D', {'weight': 5})
        graph.add_edge('D', 'A', {'weight': 5})
        graph.add_edge('A', 'D', {'weight': 5})

        graph.add_edge('1', 'B', {'weight': 1})
        graph.add_edge('B', '1', {'weight': 1})
        graph.add_edge('3', 'D', {'weight': 1})
        graph.add_edge('D', '3', {'weight': 1})
        n = Network(None)
        tt = n.travel_time(graph)
        for n in sorted(tt.iteritems(), key=operator.itemgetter(1)):
            print '%.3f' % n[1], n[0]
        print '-----------------------------------------'


def test_all():
    t = TestGraph('test_travel_time_2')
    t.test_travel_time_2()


if __name__ == '__main__':
    test_all()