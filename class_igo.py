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
        self._hways_url = highways_url
        self._cong_url = congestions_url
        self._highways = self._read_highways()
        self._add_attributes()
        #for edge, key in self._graph.edges.items():
        #    print(edge, key)
        #    print(self._graph.edges[edge]['bearing'])

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
        networkx.set_edge_attributes(self._graph, 0, "congestion")
        networkx.set_edge_attributes(self.digraph, 0, "congestion")
        networkx.set_edge_attributes(self._graph, 0, "itime") # crec que no el necessita
        networkx.set_edge_attributes(self.digraph, 0, "itime")
        networkx.set_edge_attributes(self._graph, 0, "bearing") # Edges without a bearing are laces
        networkx.set_edge_attributes(self.digraph, 0, "bearing")
        osmnx.bearing.add_edge_bearings(self._graph)
        self._add_edge_bearings_digraph() # Osmnx bearing function is only for multigraphs

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

    def print_bearings(self):
        cols = osmnx.plot.get_edge_colors_by_attr(self._graph, "bearing", num_bins=360, cmap="YlOrRd")
        osmnx.plot_graph(self._graph, edge_color=cols, edge_linewidth=2, node_size=0)

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
            #self.digraph.edges[edge]['itime'] = 2 # formula

            if 'maxspeed' in self.digraph.edges[edge]:
                speed = self.digraph.edges[edge]['maxspeed']
                if(isinstance(speed, list)):  # hi ha speeds que són llistes
                        min = 1000
                        max = 0 #we have found that the majority of edges with lists are little streets with [20,30]. There are also major streets, that's why if speed > 50 we choose the greatest speed, because there are more probabilities of having a tram there and therefore its congestion
                        for gg in speed: #all the speeds are integers
                            if int(gg) > max:
                                max = int(gg)
                            if int(gg) < min:
                                min = int(gg)
                        if max > 50:
                            speed = max
                        else:
                            speed = min

            else:
                speed = 20 #posar una velocitat predeterminada pels carrers que no en tenen al graf

            self.digraph.edges[edge]['itime'] = self.digraph.edges[edge]['length']*3.6/int(speed) * (1+self.digraph.edges[edge]['congestion']/10)
            #print(self.digraph.edges[edge]['itime'])




    """
    Given origin and destination coordinates, it calculates the shortest path
    between them taking into account the 'itime' attribute. It also calculates
    the time needed to complete the path, and it returns the path with
    information related to each node(such as its coordinates) and the total time.
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
            path_with_coordinates[-1]['osmid'] = node
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
            if node['x'] < min_x:
                min_x = node['x']
            elif node['x'] > max_x:
                max_x = node['x']
            elif node['y'] < min_y:
                min_y = node['y']
            elif node['y'] > max_y:
                max_y = node['y']
        bbox = (max_y + 0.005, min_y - 0.005, max_x + 0.005, min_x - 0.005) #+-0.005 to be able to see every node/edge completely

        route = []
        for node in path:
            route.append(node['osmid'])
        osmnx.plot_graph_route(self._graph, route, route_color = 'r', route_linewidth = 3, route_alpha = 1, node_size = 0, bgcolor='k', bbox = bbox) #route_alpha és la opacitat, close = True perquè sinó el codi no avança



# Data
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'



# Testing code
#bcn_map = iGraph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL)
#bcn_map.itime()
"""
bcn_map.print_bearings()
location1 = osmnx.geocoder.geocode("Camp Nou Barcelona")
location2 = osmnx.geocoder.geocode("Sagrada Família Barcelona")
path, time = bcn_map.get_shortest_path_with_ispeed(location1[0], location1[1], location2[0], location2[1])
bcn_map.plot_path(path)
"""


#bcn_map.print_graph()

# print(bcn_map)
# bcn_map.get_traffic()  # Actualitzar dades de tràfic
# bcn_map.print_congestions()  # Plot amb el tràfic
