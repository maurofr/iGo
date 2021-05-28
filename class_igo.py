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

Highway = collections.namedtuple('Highway', 'tram')
Congestion = collections.namedtuple('Congestion', 'tram')


class iGraph():

    # Init methods:
    def __init__(self, place, file, highways_url, congestions_url):
        if os.path.exists(file):
            with open(file, 'rb') as f:
                self._graph, self.digraph = pickle.load(f)
        else:
            self._graph = osmnx.graph_from_place(place, network_type='drive', simplify=True)
            self.digraph = osmnx.utils_graph.get_digraph(graph, weight='length')
            with open(file, 'wb') as f:
                pickle.dump([self.graph, self.digraph], f)
        self._highways_url = highways_url
        self._congestions_url = congestions_url
        self._highways = self._read_highways()
        self._add_attributes()
        self._highways_nodes = []  # Vector amb els trams de la via pública
        self._define_highways_nodes()

    def _add_edge_bearings_digraph(self):
        # extract edge IDs and corresponding coordinates from their nodes
        edges = [(u, v) for u, v in self.digraph.edges if u != v]
        x = self.digraph.nodes(data="x")
        y = self.digraph.nodes(data="y")
        coords = np.array([(y[u], x[u], y[v], x[v]) for u, v in edges])

        # calculate bearings then set as edge attributes
        bearings = osmnx.bearing.calculate_bearing(coords[:, 0], coords[:, 1], coords[:, 2], coords[:, 3])
        values = zip(edges, bearings.round(1))
        networkx.set_edge_attributes(self.digraph, dict(values), name="bearing")

    def _add_attributes(self):
        """
        It adds all the necessary attributes to the edges.
        """
        networkx.set_edge_attributes(self._graph, 0, "congestion")
        networkx.set_edge_attributes(self.digraph, 0, "congestion")
        networkx.set_edge_attributes(self._graph, 0, "itime")  # crec que no el necessita
        networkx.set_edge_attributes(self.digraph, 0, "itime")
        networkx.set_edge_attributes(self._graph, 0, "bearing")  # Edges without a bearing are laces
        networkx.set_edge_attributes(self.digraph, 0, "bearing")
        osmnx.bearing.add_edge_bearings(self._graph)
        self._add_edge_bearings_digraph()  # Osmnx bearing function is only for multigraphs

    def _add_highway(self, node1, node2):
        try:
            route1 = osmnx.shortest_path(self.digraph, node1, node2)
            route2 = osmnx.shortest_path(self.digraph, node2, node1)
            self._highways_nodes.append([route1, route2])
        except:
            self._highways_nodes.append([])

    def _define_highways_nodes(self):
        for i in range(534):
            v = self._highways[i]
            if len(v) != 0:
                node1 = osmnx.distance.nearest_nodes(self.digraph, v[0][0], v[0][1])
                node2 = osmnx.distance.nearest_nodes(self.digraph, v[-1][0], v[-1][1])
                self._add_highway(node1, node2)
            else:
                self._highways_nodes.append([])
            self._print_progress_bar(i+1, 534)
        print()  # New line after progress bar

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

    def print_bearings(self):
        cols = osmnx.plot.get_edge_colors_by_attr(self._graph, "bearing", num_bins=360, cmap="YlOrRd")
        osmnx.plot_graph(self._graph, edge_color=cols, edge_linewidth=2, node_size=0)

    def _print_progress_bar(self, iteration, total):
        """
        Prints a progress bar for the iterations of a loop.
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        fill = '█'
        percent = ("{0:." + str(1) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(100 * iteration // total)
        bar = fill * filledLength + '-' * (100 - filledLength)
        print(f'\r |{bar}| {percent}% ', end="\r")

    # Live data reading and processing methods:
    def _coordinates_transform(self, coordinates):
        """It transforms coordinates from a string into a vector
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
        with urllib.request.urlopen(self._highways_url) as response:
            lines = [l.decode('utf-8') for l in response.readlines()]
            reader = csv.reader(lines, delimiter=',', quotechar='"')
            next(reader)  # ignore first line with description
            result = [[] for _ in range(534)]
            for line in reader:
                way_id, description, coordinates = line
                result[int(way_id)-1] = self._coordinates_transform(coordinates)
                # les tres variables són strings

        return result

    def _read_congestions(self):
        with urllib.request.urlopen(self._congestions_url) as response:
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
                # way_id és de tipus list de mida 1. way_id[0] és un string
        return result

    def _update_traffic_data(self, traffic_now, tram):
        for route in tram:
            last_node = -1
            for node in route:
                if last_node != -1:
                    self._graph.edges[last_node, node, 0]["congestion"] = traffic_now
                    self.digraph.edges[last_node, node]["congestion"] = traffic_now
                last_node = node

    def get_traffic(self):
        congestions = self._read_congestions()

        for i in range(534):
            c = congestions[i]
            if len(c) != 0:
                traffic_now = int(c[-3])
                traffic_later = int(c[-1])
                self._update_traffic_data(traffic_now, self._highways_nodes[i])

    # Other methods:

    def from_location_to_node(self, lat, lon):
        """Receives the coordinates of a location and it returns its nearest node of the graph."""
        node = osmnx.distance.nearest_nodes(self.digraph, lon, lat)  # lon = 2. i lat = 41.
        return node

    def itime(self):
        """
        It adds a new attribute to every edge. This attribute is 'itime' and it
        is calculated using the speed, length and congestions on a street. It
        contains the expected time to go from the start to the end of the street.
        """
        for edge in self.digraph.edges():
            if 'maxspeed' in self.digraph.edges[edge]:
                speed = self.digraph.edges[edge]['maxspeed']
                if(isinstance(speed, list)):  # there are some speed given in lists
                        min = 1000000
                        for gg in speed:
                            if int(gg) < min:
                                min = int(gg)
                        speed = min  # we choose the slowest speed on the list
            else:
                speed = 20  # predeterminated spped

            if self.digraph.edges[edge]['congestion'] == 6:  # the street is closed
                self.digraph.edges[edge]['itime'] = 100000
            else:
                self.digraph.edges[edge]['itime'] = self.digraph.edges[edge]['length']*3.6/int(speed)
                self.digraph.edges[edge]['itime'] *= (1+self.digraph.edges[edge]['congestion']/5)**2
                self.digraph.edges[edge]['itime'] += 10

    def get_shortest_path_with_ispeed(self, origin_lat, origin_lon, destination_lat, destination_lon):
        """
        Given origin and destination coordinates, it calculates the shortest path
        between them taking into account the 'itime' attribute. It also calculates
        the time needed to complete the path, and it returns the path with
        information related to each node(such as its coordinates) and the total time.
        """
        self.itime()
        origin_node = self.from_location_to_node(origin_lat, origin_lon)
        destination_node = self.from_location_to_node(destination_lat, destination_lon)
        path = osmnx.distance.shortest_path(self.digraph, origin_node, destination_node, weight='itime')

        total_time = 0
        path_with_coordinates = []
        last_node = -1

        # now in path we have the 'number' of the nodes, but we want its coordinates, so we take each node attribute
        for node in path:
            path_with_coordinates.append(self.digraph.nodes[node])
            path_with_coordinates[-1]['node_id'] = node
            if last_node != -1:
                total_time = total_time + self.digraph.edges[last_node, node]["itime"]
            last_node = node
        return path_with_coordinates, total_time

    def plot_path(self, path):
        """
        Given a path that goes from one node to another, it calculates the minimum
        region in which the path is visible. Then, it prints the map of the city
        centered in the region, with the path visible on it.
        """
        max_x = 0
        min_x = 1000
        max_y = 0
        min_y = 1000
        for node in path:
            if node['x'] < min_x:
                min_x = node['x']
            elif node['x'] > max_x:
                max_x = node['x']
            elif node['y'] < min_y:
                min_y = node['y']
            elif node['y'] > max_y:
                max_y = node['y']
        bbox = (max_y + 0.005, min_y - 0.005, max_x + 0.005, min_x - 0.005)  # +-0.005 to be able to see every node/edge completely

        route = []
        for node in path:
            route.append(node['osmid'])
        osmnx.plot_graph_route(self._graph, route, route_color='r', route_linewidth=3,
                               route_alpha=1, node_size=0, bgcolor='k', bbox=bbox)


# Data
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'


# Testing code
# bcn_map = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL)
# bcn_map.itime()
"""
bcn_map.print_bearings()
location1 = osmnx.geocoder.geocode("Camp Nou Barcelona")
location2 = osmnx.geocoder.geocode("Sagrada Família Barcelona")
path, time = bcn_map.get_shortest_path_with_ispeed(location1[0], location1[1], location2[0], location2[1])
bcn_map.plot_path(path)
"""


# bcn_map.print_graph()

# print(bcn_map)
# bcn_map.get_traffic()  # Actualitzar dades de trànsit
# bcn_map.print_congestions()  # Plot amb el trànsit
