# -*- coding: utf-8 -*-


"""
TransNet
2014 Daniel Lamprecht
daniel.lamprecht@gmx.at
"""


from __future__ import division, unicode_literals
import re
from collections import defaultdict
import copy
from math import radians, cos, sin, asin, sqrt
import operator
import io
import random
import datetime
import pdb

import matplotlib
matplotlib.use('GTKAgg')
import matplotlib.pyplot as plt
import networkx as nx


def debug_iter(items, n=100):
    """iterate over an iterable and produce debug output"""
    for index, item in enumerate(items):
        if index % n == 0:
            print datetime.datetime.now(), index+1, '/', len(items)
        yield item


class Node(object):
    def __init__(self, id, lat, lon, name, interval=None):
        self.id = id
        self.name = name
        self.lat = float(lat)
        self.lon = float(lon)
        self.interval = interval

        
class Network(object):
    def __init__(self, filenames, lines=False):
        """
        read in the OSM data and construct the network
        lines=False: construct a directed unweighted network of the lines
        lines=True: construct a directed weighted network with lines
                    as well as transfer and travel times
        """
        if not filenames:
            print 'No files specified'
            return
        print 'building network...'

        # read data from files
        data = ''
        for f in filenames:
            with io.open(f, encoding='utf-8') as infile:
                data += infile.read()

        # extract the nodes
        name2node = {}
        id2name = {}
        nodes = re.findall(r'<node .*? </node>', data, re.DOTALL)
        re_ill = r'<node id="([0-9]+)" lat="([0-9\.]+)" lon="([0-9\.]+)"'
        re_name = r'<tag k="name" v="([^"]*)"'
        for n in nodes:
            id, lat, lon = re.findall(re_ill, n)[0]
            name = re.findall(re_name, n)
            if not name:
                continue
            name = name[0]
            n = Node(id, lat, lon, name)
            name2node[name] = n
            id2name[id] = name

        # replace some inconsistencies in the OSM data
        for old, new in [('794705419', '336334047'), ('86096405', '772629261')]:
            if old in id2name:
                id2name[new] = id2name[old]

        # extract the relations
        relations = re.findall(r'<relation .*? </relation>', data, re.DOTALL)
        self.graph = nx.MultiDiGraph()
        rel2interval = defaultdict(unicode)
        for rel in relations:
            title = re.findall(r'<tag k="ref" v="([^"]+)"', rel)
            if not title:
                continue
            title = title[0]
            skip = False
            # use only urban bus lines running during daytime
            # e.g., 30, 34E, 76U, 41/58 are okay
            # e.g., 230, 250, N5 are not
            if len(title) > 2:
                if not 'E' in title and not 'U' in title:
                    skip = True
            if 'N' in title:
                skip = True
            if len(title.split('/')) == 2 and len(title.split('/')[1]) == 2:
                skip = False
            if skip:
                continue

            # get the stops for each route and build the graph
            n_from = None
            for line in rel.split('\n'):
                if 'traveltime' in line:
                    sid = re.findall(r'ref="([0-9]+)', line)[0]
                    if sid in ['458195176']:  # fix for an OSM inconsistency
                        continue
                    if lines:
                        n_to = copy.deepcopy(name2node[id2name[sid]])
                        n_to.name += ' (' + title + ')'
                        if n_from:
                            traveltime = re.findall(r'traveltime="([0-9]+)"', line)
                            traveltime = int(traveltime[0])
                            self.graph.add_edge(n_from, n_to, weight=traveltime)
                        n_from = n_to
                    else:
                        n_to = name2node[id2name[sid]]
                        if n_from:
                            self.graph.add_edge(n_from, n_to)
                        n_from = n_to

            schedule = re.findall(r'<schedule>(.*?)</schedule>', rel)[0]
            rel2interval[title] += schedule + ' '

        if not lines:
            return

        # add stop "master" nodes for walking and transits
        # add transfer edges to the graph
        # e.g., Jakominiplatz (1) --> Jakominiplatz
        #       Jakominiplatz     --> Jakominiplatz (1)
        # edge weight: expected transfer time
        for r, s in rel2interval.items():
            # expected transfer time is half the interval
            rel2interval[r] = 60 / (len(s.split()) / 2) / 2

        node2lnode = defaultdict(list)
        for n in self.graph:
            line = n.name[n.name.rfind('('):].strip('( )')
            name = n.name[:n.name.rfind('(')][:-1]
            n.interval = rel2interval[line]
            node2lnode[name].append(n)

        self.master_nodes = []
        name2master = {}
        for k, v in node2lnode.items():
            master = copy.deepcopy(random.sample(v, 1)[0])
            master.name = master.name[:master.name.rfind('(')][:-1] + ' '
            self.master_nodes.append(master)
            name2master[master.name] = master
            for n in v:
                self.graph.add_edge(master, n, weight=n.interval)
                self.graph.add_edge(n, master, weight=0.0)

        # add virtual lines to model parallel lines
        # e.g., line "3 6" running from Jakominiplatz to Dietrichsteinplatz
        #       with the average waiting time expected when taking either 3 or 6

        # get combinations of lines actually occurring together
        common_lines = set()

        def get_connecting_lines(n, m):
            outgoing = [set(self.graph.successors(b)) for b in self.graph[n]]
            outgoing = reduce(lambda a, b: a | b, outgoing) - set([n])
            incoming = set(self.graph.predecessors(m))

            common = outgoing & incoming
            lines = set()
            if len(common) > 1:
                for nb in common:
                    if '(' in nb.name:
                        lines.add(nb.name[nb.name.rfind('('):].strip('( )'))
            return lines

        for n in self.master_nodes:
            for m in self.master_nodes:
                if n == m:
                    continue
                lines = get_connecting_lines(n, m)
                if lines:
                    common_lines.add(frozenset(lines))

        common_intervals = {}
        for cl in common_lines:
            frequency = 0
            for l in cl:
                frequency += 60 / rel2interval[l]
            common_intervals[cl] = 60 / frequency

        # connect nodes if they share any set of nodes contained in common_lines
        def connect_virtually(n, m, c):
            # create or reference adjacent nodes
            c_name = '(' + ' '.join(c) + ')'
            try:
                nb = [i for i in self.graph[n]
                      if c_name in i.name and not self.graph.successors(i)][0]
            except IndexError:
                nb = copy.deepcopy(n)
                nb.name = n.name + ' ' + c_name

            try:
                mb = [i for i in self.graph[m]
                      if c_name in i.name and not self.graph.predecessors(i)][0]
            except IndexError:
                mb = copy.deepcopy(m)
                mb.name = m.name + ' ' + c_name

            # connect nodes
            self.graph.add_edge(n, nb, weight=common_intervals[c])
            self.graph.add_edge(nb, n, weight=0.0)

            self.graph.add_edge(m, mb, weight=common_intervals[c])
            self.graph.add_edge(mb, m, weight=0.0)

            tt = nx.dijkstra_path_length(self.graph, n, m)
            self.graph.add_edge(nb, mb, weight=tt)

        for n in self.master_nodes:
            for m in self.master_nodes:
                cl = frozenset(get_connecting_lines(n, m))
                for c in common_lines:
                    if c <= cl:
                        connect_virtually(n, m, c)

        # add walking edges for nodes within a 500m distance
        speed = 4000 / 60  # meters per minute
        for n in self.master_nodes:
            for m in self.master_nodes:
                dist = self.geo_dist(n, m)
                if n == m:
                    continue
                if dist <= 500:
                    self.graph.add_edge(n, m, weight=dist/speed)
                    # print n.name, m.name, dist, dist / speed

    def print_centralities(self, nc, top=20):
        """print the nodes with the highest centrality values"""
        for n in sorted(nc.iteritems(), key=operator.itemgetter(1))[:top]:
            print '%.3f' % n[1], n[0].name
        print '-----------------------------------------'

    def closeness_centrality(self):
        """calculate the closeness centrality
        i.e., the average path length to every other network node
        """
        print '\n++++++++ closeness centrality ++++++++'
        nc = {}
        for n in self.graph:
            distances = nx.single_source_dijkstra_path_length(self.graph, n)
            nc[n] = sum(distances.values()) / len(self.graph)
        self.print_centralities(nc)

    def geo_closeness_centrality(self):
        """calculate the geographic closeness centrality
        i.e., the average path length to every other node, but with egdes
              weighted by geographic distances (bee lines)
        """
        print '\n++++++++ geographical closeness centrality ++++++++'

        graph = nx.DiGraph()
        for e, f in self.graph.edges():
            graph.add_edge(e, f, weight=self.geo_dist(e, f))
        nc = {}
        for n in graph:
            distances = nx.single_source_dijkstra_path_length(graph, n)
            nc[n] = nc[n] = sum(distances.values()) / len(self.graph)
        self.print_centralities(nc)

    def traveltime_centrality(self):
        """calculate the traveltime centrality
        i.e., the closeness centrality on the travel and transit time network
        calculate only between master nodes (and ignore auxiliary nodes)
        """
        print '\n++++++++ traveltime centrality ++++++++'
        nc = {}
        for n in debug_iter(self.master_nodes, 10):
            distances = nx.single_source_dijkstra_path_length(self.graph, n)
            distances = {k: v for k, v in distances.items()
                         if k in self.master_nodes}
            nc[n] = sum(distances.values()) / len(self.master_nodes)
        self.print_centralities(nc)

    def geo_dist(self, n, m):
        """
        calculate the (geodesic) distance between two given GPS coordinates
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [n.lon, n.lat, m.lon, m.lat])
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        km = 6367 * c
        return km * 1000


def preprocess(f):
    """
    preprocess raw OSM data and adapt it to the format used in this program
    """
    if 'tram' in f:
        role = 'stop'
    else:
        role = 'platform'

    with io.open(f, encoding='utf-8') as infile:
        data = infile.read()
    name2node = {}
    id2name = {}

    header = re.findall(r'<\?xml.*?/>', data, re.DOTALL)[0]
    nodes = re.findall(r'<node .*? </node>', data, re.DOTALL)
    re_ill = r'<node id="([0-9]+)" lat="([0-9\.]+)" lon="([0-9\.]+)"'
    re_name = r'<tag k="name" v="([^"]*)"'
    for n in nodes:
        id, lat, lon = re.findall(re_ill, n)[0]
        name = re.findall(re_name, n)
        if not name:
            continue
        name = name[0]
        name2node[name] = n
        id2name[id] = name
    # replace some inconsistencies in the OSM data
    for old, new in [('794705419', '336334047'), ('86096405', '772629261')]:
        if old in id2name:
            id2name[new] = id2name[old]

    relations = re.findall(r'<relation .*? </relation>', data, re.DOTALL)
    resolved_relations = {}
    for rel in relations:
        title = re.findall(r'<tag k="ref" v="([^"]+)"', rel)
        if not title:
            continue
        title = title[0]
        # use only urban bus lines running during daytime
        # e.g., 30, 34E, 76U, 41/58 are okay
        # e.g., 230, 250, N5 are not
        skip = False
        if len(title) > 2:
            if not 'E' in title and not 'U' in title:
                skip = True
        if 'N' in title:
            skip = True
        if len(title.split('/')) == 2 and len(title.split('/')[1]) == 2:
            skip = False
        if skip:
            continue

        lines = rel.splitlines()
        text = [lines[0]]
        tags = [l for l in lines if '<tag' in l]
        for t in tags:
            text.append(t)
        stops = [l for l in lines if 'role="' + role + '"' in l]
        for s in stops:
            sid = re.findall(r'ref="([0-9]+)"', s)[0]
            start = s.replace('role="' + role + '"/>', '')
            text.append(start + ' name="' + id2name[sid] + '" traveltime="1"/>')
        if title not in resolved_relations:
            resolved_relations[title] = '  <!-- ' + title + ' -->\n'
        resolved_relations[title] += '  ' + '\n'.join(text) +\
                                     '\n  </relation>\n'

    f_resolved = f.split('.')[0] + '_resolved.xml'
    with io.open(f_resolved, 'w', encoding='utf-8') as outfile:
        outfile.write(header + '\n')
        for n in nodes:
            outfile.write('  ' + n + '\n')
        outfile.write('\n')
        for r in sorted(resolved_relations.keys()):
            outfile.write(resolved_relations[r] + '\n')
        outfile.write('</osm>\n')


if __name__ == '__main__':

    # preprocess('data/osm_tram_raw.xml')
    # preprocess('data/osm_bus_raw.xml')
    # preprocess('data/osm_sbahn_raw.xml')

    Graz = Network([
        'data/osm_tram_traveltimes.xml',
        'data/osm_bus_traveltimes.xml',
        'data/osm_sbahn_traveltimes.xml'
    ], lines=False)
    print len(Graz.graph), 'nodes,', len(Graz.graph.edges()), 'edges'
    Graz.closeness_centrality()
    Graz.geo_closeness_centrality()

    Graz = Network([
        'data/osm_tram_traveltimes.xml',
        'data/osm_bus_traveltimes.xml',
        'data/osm_sbahn_traveltimes.xml'
    ], lines=True)
    print len(Graz.graph), 'nodes,', len(Graz.graph.edges()), 'edges'
    Graz.traveltime_centrality()

