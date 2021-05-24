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
import random

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
        self._add_attributes()

    def _add_attributes(self):
        networkx.set_edge_attributes(self._graph, 0, "congestion")
        networkx.set_edge_attributes(self.digraph, 0, "congestion")
        networkx.set_edge_attributes(self._graph, 0, "itime") # crec que no el necessita
        networkx.set_edge_attributes(self.digraph, 0, "itime")

    # Output methods:
    def __str__(self):
        out = ""
        for node1, info1 in self.digraph.nodes.items():
            out += "Node: "
            out += str(node1)
            out += str(info1)
            out += "\n"
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
                way_id, description, coordinates = line
                result[int(way_id)-1] = self._coordinates_transform(coordinates)
                #les tres variables són strings

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
                #way_id és de tipus list de mida 1. way_id[0] és un string
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

    def _add_tram(self, trams, node1, node2, traffic_now): # Tram en angles? xD
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
        node = osmnx.distance.nearest_nodes(self.digraph, lon, lat) #lon = 2. i lat = 41.
        return node


    def itime(self):
        for edge in self.digraph.edges():
            self.digraph.edges[edge]['itime'] = 2 # formula
            #print(self.digraph.edges[edge]['itime'])
            #print(self.digraph.edges[edge]['length'])
            if 'maxspeed' in self.digraph.edges[edge]:
                speed = self.digraph.edges[edge]['maxspeed']
            else:
                self.digraph.edges[edge]['maxspeed'] = 20 #posar una velocitat predeterminada pels carrers que no en tenen al graf
            if(isinstance(speed, list)):  # hi ha speeds que són llistes
                    print(speed)


    """
    Given origin and destination coordinates, it calculates the shortest path
    between them. It also calculates the time needed to complete the path,
    and it returns the path with information related to each node(such as its
    coordinates) and the total time.
    """
    def get_shortest_path_with_ispeed(self, origin_lat, origin_lon, destination_lat, destination_lon):
        self.itime()
        origin_node = self.from_location_to_node(origin_lat, origin_lon)
        destination_node = self.from_location_to_node(destination_lat, destination_lon)
        path = osmnx.distance.shortest_path(self.digraph, origin_node, destination_node, weight = 'itime')

        #now in path we have the 'number' of the nodes, but we want its coordinates, so we take each node attribute
        total_time = 0
        path_with_coordinates = []
        last_node = -1
        for node in path:
            path_with_coordinates.append(self.digraph.nodes[node])
            if last_node != -1:
                total_time = total_time + self.digraph.edges[last_node, node]["itime"]
            last_node = node
        return path_with_coordinates, total_time #this will return a list of lists of the nodes constituting the shortest path between each origin-destination pair. If a path cannot be solved, this will return None for that path

    """
    Given a path that goes from one node to another, it calculates the minimum
    region in which the path is visible. Then, it prints the map of the city
    centered in the region, with the path visible on it.
    """
    def plot_path(self, path): #també es poden fer dues funcions, una que doni el mapa centrat i l'altre que doni el mapa complet
        max_x = 0
        min_x = 1000
        max_y = 0
        min_y = 1000
        for node in path:
            print(self.digraph.nodes[node])
            if self.digraph.nodes[node]['x'] < min_x:
                min_x = self.digraph.nodes[node]['x']
            elif self.digraph.nodes[node]['x'] > max_x:
                max_x = self.digraph.nodes[node]['x']
            elif self.digraph.nodes[node]['y'] < min_y:
                min_y = self.digraph.nodes[node]['y']
            elif self.digraph.nodes[node]['y'] > max_y:
                max_y = self.digraph.nodes[node]['y']
        bbox = (max_y + 0.005, min_y - 0.005, max_x + 0.005, min_x - 0.005) #+-0.005 to be able to see every node/edge completely

        osmnx.plot_graph_route(self._graph, path, route_color = 'r', route_linewidth = 3, route_alpha = 1, node_size = 0, bgcolor='k', bbox = bbox) #route_alpha és la opacitat, close = True perquè sinó el codi no avança



# Data
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'



# Code
"""
bcn_map = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL)
location1 = osmnx.geocoder.geocode("Camp Nou Barcelona")
location2 = osmnx.geocoder.geocode("Sagrada Família Barcelona")
path = bcn_map.get_shortest_path_with_ispeed(location1[0], location1[1], location2[0], location2[1])
bcn_map.plot_path(path)
"""

#bcn_map.print_graph()

# print(bcn_map)
# bcn_map.get_traffic()  # Actualitzar dades de tràfic
# bcn_map.print_congestions()  # Plot amb el tràfic
