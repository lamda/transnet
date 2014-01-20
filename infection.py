<<<<<<< HEAD
# -*- coding: utf-8 -*-


"""
Transnet
2013 Daniel Lamprecht
daniel.lamprecht@gmx.at
"""

from __future__ import division
import pdb
import networkx as nx
import matplotlib
matplotlib.use('GTKAgg')
import matplotlib.pyplot as plt
import prettyplotlib as ppl
import numpy as np
from collections import deque
import random
from joblib import Parallel, delayed

from main import Network
import schedules


def bfs_spread(graph, start_name):
    name2node = {n.name: n for n in graph.nodes()}
    #node2name = {n: n.name for n in graph.nodes()}
    start = [name2node[s] for s in start_name]
    tree = nx.DiGraph()
    for s in start:
        tree.add_node(s)
    tree.add_edges_from(bfs_edges(graph, start))
    #name2treenode = {n.name: n for n in tree.nodes()}
    #treenode2name = {n: n.name for n in tree.nodes()}
    spread = [1]
    old_fringe = set(start)
    fringe = set()

    while old_fringe:
        for n in old_fringe:
            for m in (k for k in tree[n]):
                fringe.add(m)
        spread.append(len(fringe) + spread[-1])
        old_fringe = fringe
        fringe = set()
    return (start_name, spread[:-1])


def bfs_edges(G, source):
    """Produce edges in a breadth-first-search starting at source."""
    # Based on networkx.algorithms.traversal.breadth_first_search
    # adapted by Daniel Lamprecht
    neighbors = G.neighbors_iter
    #visited = set([source])
    #queue = deque([(source, neighbors(source))])
    visited = set()
    queue = deque()
    for s in source:
        visited.add(s)
        queue.append((s, neighbors(s)))
    while queue:
        parent, children = queue[0]
        try:
            child = next(children)
            if child not in visited:
                yield parent, child
                visited.add(child)
                queue.append((child, neighbors(child)))
        except StopIteration:
            queue.popleft()

if __name__ == '__main__':
    # single
    '''
    graph = Network(['data/osm_tram_bus.xml', 'data/osm_sbahn.xml']).graph
    name2node = {n.name: n for n in graph.nodes()}
    start_names = [['Jakominiplatz'], ['Don Bosco'], ['St. Leonhard/LKH']]
    results = [(s, bfs_spread(graph, s)) for s in start_names]
    results_rand = Parallel(n_jobs=7)(delayed(bfs_spread)(graph, [p]) for p in name2node.keys())
    results_rand = [(r[0][0], r[1]) for r in results_rand]
    #results_rand2 = [(s, bfs_spread(graph, [s])[1]) for s in name2node.keys()]
    res_len = sorted(results_rand, key=lambda r: len(r[1]))
    slowest = (['Slowest (' + unicode(res_len[-1][0]) + ')'], res_len[-1][1])

    maxlen = max(len(r[1]) for r in results_rand)
    results_rand_new = []
    for r in results_rand:
        results_rand_new.append((r[0], r[1] + (maxlen - len(r[1])) * [r[1][-1]]))
    results_rand = results_rand_new
    results_new = []
    for r in results:
        results_new.append((r[0], r[1] + (maxlen - len(r[1])) * [r[1][-1]]))
    results = results_new

    val_av = sum(np.array(r[1]) for r in results_rand) / len(results_rand)
    average = (['Average'], val_av)

    toplot = results + [average, slowest]
    toplot_new = []
    for t in toplot:
        nor = [100 * v / len(graph) for v in t[1]]
        toplot_new.append((t[0], nor))
    toplot = toplot_new
    fig, ax = plt.subplots(1)
    for label, data in toplot:
        ppl.plot(ax, np.arange(len(data)), data, label=label[0], linewidth=2.5)
    ppl.legend(ax, loc=0)
    plt.xlabel('#Hops')
    plt.ylabel('% of the Network')
    plt.ylim(0, 110)
    plt.xlim(0, 50)
    plt.title('Spread on the network, based on one source')
    plt.savefig('plot_1.png')
    #'''
    # double
    '''
    graph = Network(['data/osm_tram_bus.xml', 'data/osm_sbahn.xml']).graph
    name2node = {n.name: n for n in graph.nodes()}
    node2name = {n: n.name for n in graph.nodes()}
    start_names = [['St. Leonhard/LKH', 'Eggenberg/UKH']]
    results = [(s, bfs_spread(graph, s)) for s in start_names]
    pairs = []
    for i, s in enumerate(graph.nodes()):
        for j, t in enumerate(graph.nodes()[i+1:]):
        #for t in ['Tiefenbachstraße', 'Don Bosco']:
            #if node2name[s] != t:
            pairs.append((node2name[s], node2name[t]))

    results_rand = []
    #pairs_s = random.sample(pairs, 2500)
    #for i, s in enumerate(pairs):
    #    if not i % 1000:
    #        print 100 * (i + 1) / len(pairs), '%'
    #    results_rand.append((s, bfs_spread(graph, s)))

    results_rand = Parallel(n_jobs=2)(delayed(bfs_spread)(graph, p) for p in pairs)

    res_len = sorted(results_rand, key=lambda r: len(r[1]))
    label = u'\n'.join([unicode(h) for h in res_len[-1][0]])
    slowest = (['Slowest \n(' + label + ')'], res_len[-1][1])
    label = u'\n'.join([unicode(h) for h in res_len[0][0]])
    fastest = (['Fastest \n(' + label + ')'], res_len[0][1])


    maxlen = max(len(r[1]) for r in results_rand)
    results_rand_new = []
    for r in results_rand:
        results_rand_new.append((r[0], r[1] + (maxlen - len(r[1])) * [r[1][-1]]))
    results_rand = results_rand_new
    results_new = []
    for r in results:
        results_new.append((r[0], r[1] + (maxlen - len(r[1])) * [r[1][-1]]))
    results = results_new

    val_av = sum(np.array(r[1]) for r in results_rand) / len(results_rand)
    average = (['Average'], val_av)

    toplot = results + [average, slowest, fastest]
    toplot_new = []
    for t in toplot:
        nor = [100 * v / len(graph) for v in t[1]]
        toplot_new.append((t[0], nor))
    toplot = toplot_new
    fig, ax = plt.subplots(1)
    for label, data in toplot:
        ppl.plot(ax, np.arange(len(data)), data, label='\n'.join(label), linewidth=2.5)
    ppl.legend(ax, loc=0)
    plt.xlabel('#Hops')
    plt.ylabel('% of the Network')
    plt.ylim(0, 110)
    plt.xlim(0, 50)
    plt.title('Spread on the network, based on two sources')
    plt.savefig('plot_2.png')
    '''
    # triple
    #'''
    graph = Network(['data/osm_tram_bus.xml', 'data/osm_sbahn.xml']).graph
    name2node = {n.name: n for n in graph.nodes()}
    node2name = {n: n.name for n in graph.nodes()}
    start_names = [['St. Leonhard/LKH', 'Eggenberg/UKH', 'Wagner-Jauregg-Platz']]
    results = [bfs_spread(graph, s) for s in start_names]
    pairs = []
    for i, s in enumerate(graph.nodes()):
        for j, t in enumerate(graph.nodes()[i+1:]):
            for k, u in enumerate(graph.nodes()[i+1+j+1:]):
                pairs.append((node2name[s], node2name[t], node2name[u]))

    pairs = random.sample(pairs, 10000)
    results_rand = Parallel(n_jobs=7, verbose=1)(delayed(bfs_spread)(graph, p) for p in pairs)
    results_rand = [(r[0], r[1]) for r in results_rand]
    res_len = sorted(results_rand, key=lambda r: len(r[1]))
    label = u'\n'.join([unicode(h) for h in res_len[-1][0]])
    #label = res_len[-1][0]
    slowest = (['Slowest \n(' + label + ')'], res_len[-1][1])
    label = u'\n'.join([unicode(h) for h in res_len[0][0]])
    #label = res_len[0][0][0]
    fastest = (['Fastest \n(' + label + ')'], res_len[0][1])

    maxlen = max(len(r[1]) for r in results_rand)
    results_rand_new = []
    for r in results_rand:
        results_rand_new.append((r[0], r[1] + (maxlen - len(r[1])) * [r[1][-1]]))
    results_rand = results_rand_new
    results_new = []
    for r in results:
        results_new.append((r[0], r[1] + (maxlen - len(r[1])) * [r[1][-1]]))
    results = results_new

    val_av = sum(np.array(r[1]) for r in results_rand) / len(results_rand)
    average = (['Average'], val_av)

    toplot = results + [average, slowest, fastest]
    toplot_new = []
    for t in toplot:
        nor = [100 * v / len(graph) for v in t[1]]
        toplot_new.append((t[0], nor))
    toplot = toplot_new
    fig, ax = plt.subplots(1)
    for label, data in toplot:
        ppl.plot(ax, np.arange(len(data)), data, label='\n'.join(label), linewidth=2.5)
    ppl.legend(ax, loc=0)
    plt.xlabel('#Hops')
    plt.ylabel('% of the Network')
    plt.ylim(0, 110)
    plt.xlim(0, 50)
    plt.title('Spread on the network, based on two sources')
    plt.savefig('plot_3.png')
    #'''
=======
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
>>>>>>> origin/master
