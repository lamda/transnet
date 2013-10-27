# -*- coding: utf-8 -*-


import pdb
import re
import urllib2
import networkx as nx
import cPickle as pickle
import operator
import matplotlib.pyplot as plt

import stops


class Network(object):
    label = ''
    graphs = None

    def __init__(self):
        pass

    def save(self, graphs):
        with open(self.label + '.obj', 'wb') as outfile:
            pickle.dump(graphs, outfile, -1)

    def load(self):
        with open(self.label + '.obj', 'rb') as outfile:
            graphs = pickle.load(outfile)
        self.graphs = graphs

    def centralities(self):
        for graph, label in zip(self.graphs, ['tram', 'bus']):
            print '+++++++++++++++++++++++++++++++++++++++++++++'
            print label
            for c in [nx.degree_centrality, nx.closeness_centrality,
                      nx.betweenness_centrality,
                      nx.edge_betweenness_centrality,
                      nx.eigenvector_centrality_numpy, nx.pagerank]:
                #nodes = c(self.graphs[0])
                nodes = c(graph)
                print c.__name__
                print
                for n in sorted(nodes.iteritems(), key=operator.itemgetter(1),
                                reverse=True)[:5]:
                    print '%.3f' % n[1], n[0]
                print '-----------------------------------------'


class Vienna(Network):
    label = 'vienna'

    def __init__(self):
        pass


class Graz(Network):
    label = 'graz'

    def __init__(self):
        pass

    def crawl(self):
        tram_lines = ['1', '3', '4', '5', '6', '7']
        tram_url = 'http://www.holding-graz.at/linien/fahrplaene/bim/linie-'
        self.graphs.append(nx.DiGraph())
        for line in tram_lines:
            url = tram_url + line + '.html'
            print line, url
            data = urllib2.urlopen(url)
            data = data.read()
            stops = re.findall(r'#"><strong>([^</]*)', data)
            stops = [s.strip() for s in stops]
            stops = [s.decode('utf-8') for s in stops]
            for s, t in zip(stops, stops[1:]):
                # trams always use the same stops for both directions
                self.graphs[-1].add_edge(s, t)
                self.graphs[-1].add_edge(t, s)


        bus_lines = ['E', 'E5', '30', '31', '32', '33', '33E', '34', '34E',
                     '39', '40', '4153', '48', '50', '52', '53', '58', '60',
                     '62', '63', '64', '64E', '65', '65E', '67', '67E', '74',
                     '77', '85']
        bus_url = 'http://www.holding-graz.at/linien/fahrplaene/bus/linie-'
        graphs = [nx.Graph(), nx.Graph()]

        # manually add non HGL bus lines
        graph = graphs[1]
        #35
        # TODO: directed lines (Wielandgasse Süd)

        self.save(graphs)

    def load_txt_stops(self):
        # TODO: find similar sounding stops, à la Don Bosco - Don Bosco Bahnhof
        tram_graph = nx.DiGraph()
        for line in stops.tram_stops:
            for s, t in zip(line, line[1:]):
                tram_graph.add_edge(s, t)

        bus_graph = nx.DiGraph()
        bus_graph = tram_graph.copy()
        for line in stops.bus_stops:
            for s, t in zip(line, line[1:]):
                bus_graph.add_edge(s, t)

        self.graphs = [tram_graph, bus_graph]


def main():
    graz = Graz()
    graz.load_txt_stops()
    #graz.crawl()

    #graz.load()
    graz.centralities()

    #nx.draw(graz.graphs[0]); plt.show()


if __name__ == '__main__':
    main()