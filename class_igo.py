import collections
import csv
import pickle
import urllib
import networkx
import osmnx
import haversine
import staticmap
import matplotlib.pyplot as plt
import numpy as np
import os

# This is what an implementation of the code with a class would look like.
# It still has to be finished, but gives an idea of how it can be beneficial
# with respect to an "only-functions" implementation.

Highway = collections.namedtuple('Highway', 'tram')  # Tram
Congestion = collections.namedtuple('Congestion', 'tram')


class iGraph():

    def __init__(self, place, file, highways_url, congestions_url):
        if os.path.exists(file):
            with open(file, 'rb') as f:
                self._graph, self.digraph = pickle.load(f)
        else:
            self._graph = osmnx.graph_from_place(place, network_type='drive', simplify=True)
            self.digraph = osmnx.utils_graph.get_digraph(graph, weight='length')
            with open(file, 'wb') as f:
                pickle.dump([self.graph, self.digraph], f)
        self._hways_url = highways_url
        self._cong_url = congestions_url
        self._highways = self._read_highways()
        self._add_congestion_attribute()

    def _add_congestion_attribute(self):
        networkx.set_edge_attributes(self._graph, 0, "congestion")
        networkx.set_edge_attributes(self.digraph, 0, "congestion")

    # Output methods:
    def __str__(self):
        out = ""
        for node1, info1 in self.digraph.nodes.items():
            out += "Node: "
            out += str(node1)
            out += str(info1)
            out += "\n"

            # for each adjacent node and its information...
            for node2, edge in self.digraph.adj[node1].items():
                out += "    Goes to node: "
                out += str(node2)
                out += ", through the edge: "
                out += str(edge)
                out += "\n"
            out += "\n"
        return out

    def __repr__(self):
        return self.__str__()

    def print_graph(self):
        osmnx.plot_graph(self._graph)

    def print_congestions(self):
        ec = osmnx.plot.get_edge_colors_by_attr(self._graph, "congestion", cmap="YlOrRd")
        osmnx.plot_graph(self._graph, edge_color=ec, edge_linewidth=2, node_size=0)

    def print_highways(self):
        #fer algo
        return

    # Live data reading and processing methods:
    def _coordinates_transform(self, coordinates):
        """transforms coordinates from a string into a vector
        in which every position is a coordinate"""
        v = []
        s = ""
        pair = []
        for i in coordinates:
            if i == ",":
                if(len(pair) == 2):
                    v.append(pair)
                    pair = []

                pair.append(float(s))
                s = ""
            else:
                s = s + i
        pair.append(float(s))
        v.append(pair)
        return v

    def _read_highways(self):
        with urllib.request.urlopen(self._hways_url) as response:
            lines = [l.decode('utf-8') for l in response.readlines()]
            reader = csv.reader(lines, delimiter=',', quotechar='"')
            next(reader)  # ignore first line with description
            result = [[] for _ in range(534)]
            for line in reader:
                v = []
                way_id, description, coordinates = line
                v.append(way_id)
                v.append(description)
                v.append(coordinates)
                result[int(way_id)-1] = self._coordinates_transform(coordinates)
                # result.append(v)
                # print(way_id, description, coordinates) #les tres variables són strings

        return result

    def _read_congestions(self):
        with urllib.request.urlopen(self._cong_url) as response:
            lines = [l.decode('utf-8') for l in response.readlines()]
            reader = csv.reader(lines, delimiter=',', quotechar='"')
            # next(reader)  # ignore first line with description   en aquest cas la primera linia no s'ha d'ignorar
            result = ["" for _ in range(534)]
            for line in reader:
                way_id = line
                i = 0
                while way_id[0][i] != '#':
                    i += 1
                result[int(way_id[0][0:i]) - 1] = way_id[0]
                # print(way_id[0]) #way_id és de tipus list de mida 1. way_id[0] és un string
        return result

    def _add_traffic_data(self, route, traffic_now):
        last_node = -1
        for node in route:
            if last_node != -1:
                self._graph.edges[last_node, node, 0]["congestion"] = max(
                    self._graph.edges[last_node, node, 0]["congestion"], traffic_now)
                self.digraph.edges[last_node, node]["congestion"] = max(
                    self.digraph.edges[last_node, node]["congestion"], traffic_now)
            last_node = node

    def _add_tram(self, trams, node1, node2, traffic_now):
        try:
            route1 = osmnx.shortest_path(self.digraph, node1, node2)
            route2 = osmnx.shortest_path(self.digraph, node2, node1)
            trams.append(route1)
            self._add_traffic_data(route1, traffic_now)
            self._add_traffic_data(route2, traffic_now)
            trams.append(route2)
        except:
            pass

    def get_traffic(self):
        congestions = self._read_congestions()

        trams = []  # Vector amb els trams de la via pública
        for i in range(534):
            v = self._highways[i]
            c = congestions[i]
            if len(v) != 0 and len(c) != 0:
                node1 = osmnx.distance.nearest_nodes(self.digraph, v[0][0], v[0][1])
                node2 = osmnx.distance.nearest_nodes(self.digraph, v[-1][0], v[-1][1])
                traffic_now = int(c[-3])
                traffic_later = int(c[-1])
                self._add_tram(trams, node1, node2, traffic_now)

    # Other methods:
    """Receives the coordinates of a location and it returns its nearest node of the graph."""
    def from_location_to_node(self, lat, lon):
        node = osmnx.distance.nearest_nodes(self.digraph, lat, lon) #vigilar amb lo de lat i lon, que potser estan en ordre equivocat
        print(self.digraph.nodes[node])
        return node #???


    def itime(self):
        for node1, info1 in self._graph.nodes.items():
            # print(node1, info1) #type(info1) = dictionary, list(info1) et diu les keys que té
            # print(graph[node1])
            # print(info1)
            # for each adjacent node and its information...
            for node2, edge in self._graph.adj[node1].items():
                if "maxspeed" in edge[0]:
                    speed = edge[0]["maxspeed"]
                else:
                    speed = 1  # posar una velocitat predeterminada
                length = edge[0]["length"]  # en teoria tots els edges tenen length

                if "congestion" in edge[0]:
                    print(True)  # speed = speed / algo ??

                # print(float(length))
                if(isinstance(speed, list)):  # hi ha speeds que són llistes
                    print(speed)
                # print(float(speed))
                # print(time)

                # print('    ', node2)
                # print(edge)
                # print('        ', list(edge[0])) #imprimeix tots els atributs dels edges
                # print(list(graph.edges[node1, node2, 0])) #fa el mateix que la línia de sobre

        def get_shortest_path_with_ispeed(self, origin_lat, origin_lon, destination_lat, destination_lon):
            itime(self)
            origin_node = from_location_to_node(origin_lat, origin_lon)
            destination_node = from_location_to_node(destination_lat, destination_lon)
            path = osmnx.distance.shortest_path(self.digraph, origin_node, destination_node, weight = 'itime')
            return path #this will return a list of lists of the nodes constituting the shortest path between each origin-destination pair. If a path cannot be solved, this will return None for that path

        def plot_path(self, path):
            return


# Data
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

# Code
bcn_map = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL)
#bcn_map.print_graph()

# print(bcn_map)
# bcn_map.get_traffic()  # Actualitzar dades de tràfic
# bcn_map.print_congestions()  # Plot amb el tràfic
