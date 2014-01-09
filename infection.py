# -*- coding: utf-8 -*-


"""
Transnet
2013 Daniel Lamprecht
daniel.lamprecht@gmx.at
"""

import pdb
import networkx as nx
import matplotlib
matplotlib.use('GTKAgg')
import matplotlib.pyplot as plt
import matplotlib as mpl
import prettyplotlib as ppl
import numpy as np

from main import Network


def bfs_spread(start_name):
    name2node = {n.name: n for n in graph.nodes()}
    node2name = {n: n.name for n in graph.nodes()}
    start = name2node[start_name]
    tree = nx.bfs_tree(graph, start)
    name2treenode = {n.name: n for n in tree.nodes()}
    treenode2name = {n: n.name for n in tree.nodes()}
    spread = [1]
    visited = set()
    old_fringe = set([start])
    fringe = set()
    while old_fringe:
        for n in old_fringe:
            for m in (k for k in tree[n]):
                fringe.add(m)
        spread.append(len(fringe) + spread[-1])
        old_fringe = fringe
        fringe = set()
    spread = spread[:-1]
    return spread

if __name__ == '__main__':
    graph = Network(['data/osm_tram_bus.xml', 'data/osm_sbahn.xml']).graph
    start_names = ['Jakominiplatz', 'Don Bosco', 'Geidorfplatz']
    results = [(s, bfs_spread(s)) for s in start_names]

    fig, ax = plt.subplots(1)
    for label, data in results:
        ppl.plot(ax, np.arange(len(data)), data, label=label, linewidth=2.5)
    ppl.legend(ax)
    plt.show()
