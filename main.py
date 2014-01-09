# -*- coding: utf-8 -*-


"""
Transnet
2013 Daniel Lamprecht
daniel.lamprecht@gmx.at
"""


from __future__ import division
import re
import networkx as nx
from math import radians, cos, sin, asin, sqrt
import operator
import pdb

from intervals import get_interval


class Node(object):
    def __init__(self, id, lat, lon, name):
        self.id = id
        self.name = name
        self.lat = float(lat)
        self.lon = float(lon)

        
class Network(object):
    def __init__(self, filenames):
        """
        reads in the OSM data and constructs the network (saved in self.graph)
        """
        # read data from files
        data = ''
        for f in filenames:
            with open(f) as infile:
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

        # Hack to replace some inconsistencies in the OSM data
        for old, new in [('794705419', '336334047'), ('86096405', '772629261')]:
            if old in id2name:
                id2name[new] = id2name[old]

        # extract the relations
        relations = re.findall(r'<relation .*? </relation>', data, re.DOTALL)
        titles = []
        self.graph = nx.DiGraph()
        for rel in relations:
            title = re.findall(r'<tag k="ref" v="([^"]+)"', rel)
            if not title:
                continue
            title = title[0]
            if title in ['26', '13', '65E', '64E', '33E', '41/53', '58E', '82',
                         '74E', ]:
                # ignore a few redundant lines (for the network)
                continue
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
            stops = []
            for line in rel.split('\n'):
                if '<tag k="route" v="tram"/>' in rel:
                    keyword = 'role="stop"'
                else:
                    keyword = 'role="platform"'
                if keyword in line:
                    id = re.findall(r'ref="([0-9]+)', line)[0]
                    if id in ['458195176']:  # OSM inconsistency
                        continue
                    stops.append(id)
            for a, b in zip(stops, stops[1:]):
                n, m = name2node[id2name[a]], name2node[id2name[b]]
                self.graph.add_edge(n, m)
            titles.append(title)
        #################
        #print set(titles) -\
        #set(infections.bus_inputs.keys()) | set(infections.tram_inputs.keys()))
        #################

    def centralities(self):
        """
        calculates several centrality measures on the network
        """
        for c in [nx.betweenness_centrality, nx.eigenvector_centrality_numpy,
                  self.beeline, self.beeline_intermediate]:
            nodes = c(self.graph)
            print c.__name__
            print
            rev = True
            if c in [self.beeline, self.beeline_intermediate]:
                rev = False
            for n in sorted(nodes.iteritems(), key=operator.itemgetter(1),
                            reverse=rev)[:5]:
                print '%.3f' % n[1], n[0].name
            print '-----------------------------------------'
        
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
        for n in graph:
            nc[n] = 0
            for m in graph:
                nc[n] += self.geo_dist_sp(n, m)
        
        for n in nc:
            nc[n] /= len(graph)
        
        return nc
        
    def geo_dist(self, n, m):
        """
        calculates the (geodisic) distance between two GPS coordinates
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
        like self.geo_dist, calculates the (geodisic) distance between two GPS
        coordinates but by using all intermediate stops, e.g., not the distance
        A-B but e.g., A-C-D-E-B
        """
        sp = nx.shortest_path(self.graph, n, m)
        dist = 0
        for a, b in zip(sp, sp[1:]):
            dist += self.geo_dist(a, b)
        return dist            
            

if __name__ == '__main__':
    '''Graz_tram = Network(['data/osm_tram.xml'])
    print len(Graz_tram.graph), len(Graz_tram.graph.edges())
    Graz_tram.centralities()

    print '########################################################'
    
    Graz = Network(['data/osm_tram_bus.xml'])
    print len(Graz.graph), len(Graz.graph.edges())
    Graz.centralities()
    
    print '########################################################'
    '''
    Graz_complete = Network(['data/osm_tram_bus.xml', 'data/osm_sbahn.xml'])
    print len(Graz_complete.graph), len(Graz_complete.graph.edges())
    Graz_complete.centralities()
