# -*- coding: utf-8 -*-


"""
Transnet
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
import datetime
import pdb

import networkx as nx


def debug_iter(items, n=100):
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
    def __init__(self, filenames):
        """
        reads in the OSM data and constructs the network (saved in self.graph)
        """
        if not filenames:
            return
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
        self.graph = nx.DiGraph()
        rel2interval = defaultdict(unicode)
        for rel in relations:
            title = re.findall(r'<tag k="ref" v="([^"]+)"', rel)
            if not title:
                continue
            title = title[0]
            # if title in ['65E', '64E', '33E', '41/53', '58E', '82', '74E']:
            #     # ignore a few redundant lines
            #     continue
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
            keyword = 'traveltime'

            n_from = None
            for line in rel.split('\n'):
                if keyword in line:
                    sid = re.findall(r'ref="([0-9]+)', line)[0]
                    if sid in ['458195176']:  # OSM inconsistency
                        continue
                    n_to = copy.deepcopy(name2node[id2name[sid]])
                    n_to.name += ' (' + title + ')'
                    if n_from:
                        traveltime = re.findall(r'traveltime="([0-9]+)"', line)
                        traveltime = int(traveltime[0])
                        suffix = ' (' + title + ')'
                        self.graph.add_edge(n_from, n_to, weight=traveltime)
                    n_from = n_to

            schedule = re.findall(r'<schedule>(.*?)</schedule>', rel)[0]
            rel2interval[title] += schedule + ' '

        # add transfer edges to the graph
        # e.g., Jakominiplatz (1) --> Jakominiplatz (3)
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

        for k, v in node2lnode.items():
            for n in v:
                for m in v:
                    if n == m:
                        continue
                    self.graph.add_edge(n, m, weight=m.interval)

    def centralities(self):
        """
        calculates several centrality measures on the network
        """
        for c in [
            #nx.betweenness_centrality,
            #nx.eigenvector_centrality_numpy,
            self.beeline,
            #self.beeline_intermediate,
            self.travel_time
        ]:
            nodes = c(self.graph)
            print c.__name__
            rev = True
            topn = 20
            if c in [self.beeline, self.beeline_intermediate, self.travel_time]:
                rev = False
            # for n in sorted(nodes.iteritems(), key=operator.itemgetter(1),
            #                 reverse=rev)[:topn]:
            #     print '%.3f' % n[1], n[0].name
            # print '-----------------------------------------'

            #  for several stops sharing a name, take only the maximum
            #  restructure the dictionary accordingly
            d = defaultdict(float)
            for n in sorted(nodes.iteritems(), key=operator.itemgetter(1),
                            reverse=rev):
                stop = n[0].name[:n[0].name.rfind('(')].strip()
                if d[stop] < n[1]:
                    d[stop] = n[1]

            for k, v in sorted(d.iteritems(), key=operator.itemgetter(1),
                               reverse=rev)[:topn]:
                print '%.3f' % v, k
            print '-----------------------------------------\n'

    def beeline(self, graph):
        """
        calculates the average beeline between all pairs of stops in the network
        """
        nc = {}
        for n in graph:
            nc[n] = 0
            for m in graph:
                nc[n] += self.geo_dist(n, m)
        
        for n in nc:
            nc[n] /= len(graph)
        
        return nc

    def beeline_intermediate(self, graph):
        """
        similar to self.beeline(), calculates the average beeline between all
        pairs of stops in the network but instead of calculating the beeline
        between nodes A and B directly, it calculates the beeline between all
        intermediate stops, e.g., A-C-D-E-B
        """
        nc = {}
        for n in debug_iter(graph, 1):
            nc[n] = 0
            for m in graph:
                nc[n] += self.geo_dist_sp(n, m)
        
        for n in nc:
            nc[n] /= len(graph)
        
        return nc
        
    def geo_dist(self, n, m):
        """
        calculates the (geodesic) distance between two GPS coordinates
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
        
    def geo_dist_sp(self, n, m):
        """
        like self.geo_dist, calculates the (geodesic) distance between two GPS
        coordinates but by using all intermediate stops, e.g., not the distance
        A-B but e.g., A-C-D-E-B
        """
        sp = nx.shortest_path(self.graph, n, m)
        dist = 0
        for a, b in zip(sp, sp[1:]):
            dist += self.geo_dist(a, b)
        return dist            

    def travel_time(self, graph):
        nc = {}
        for n in debug_iter(graph, 1):
            distances = nx.single_source_dijkstra_path_length(self.graph, n)
            nc[n] = self.sum_filter_stops(distances)
        for n in nc:
            nc[n] += n.interval
            nc[n] /= len(graph)
        return nc

    def sum_filter_stops(self, dists):
        d = {}
        for k, v in dists.items():
            stop = k.name[:k.name.rfind('(')].strip()
            # TODO are names unambiguous?
            if not stop in d or d[stop] > v:
                d[stop] = v
        return sum(d.values())


def preprocess(f):
    if 'tram' in f:
        role = 'stop'
    else:
        role='platform'

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
        resolved_relations[title] += '  ' + '\n'.join(text) + '\n  </relation>\n'

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

    # preprocess('data/osm_tram.xml')
    # preprocess('data/osm_bus.xml')
    # preprocess('data/osm_sbahn.xml')

    Graz = Network([
        'data/osm_tram_traveltimes.xml',
        'data/osm_bus_traveltimes.xml',
        'data/osm_sbahn_traveltimes.xml'
    ])
    print len(Graz.graph), 'nodes,', len(Graz.graph.edges()), 'edges\n'
    Graz.centralities()
