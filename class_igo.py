import staticmap
import matplotlib.pyplot as plt
import numpy as np
import os

# This is what an implementation of the code with a class would look like.
# It still has to be finished, but gives an idea of how it can be beneficial
# with respect to an "only-functions" implementation.

Highway = collections.namedtuple('Highway', 'tram')  # Tram
Congestion = collections.namedtuple('Congestion', 'tram')


class geo_graph():

    def __init__(self, place, file, highways_url, congestions_url):
        if os.path.exists(file):
            with open(file, 'rb'):
                self.graph, self.digraph = pickle.load(file)
        else:
            self.graph = osmnx.graph_from_place(place, network_type='drive', simplify=True)
            self.digraph = osmnx.utils_graph.get_digraph(graph, weight='length')
            with open(file, 'wb'):
                pickle.dump([self.graph, self.digraph], file)
        self._hways_url = highways_url
        self._cong_url = congestions_url


    # for each node and its information...
    def print_graph(self):
        for node1, info1 in graph.nodes.items():
            # print(node1, info1) #type(info1) = dictionary, list(info1) et diu les keys que té
            print(graph[node1])
            print(info1)
            """
            # for each adjacent node and its information...
            for node2, edge in graph.adj[node1].items():
                print('    ', node2)
                print('        ', edge) #type(edge) = dictionary
            """

    def coordinates_transform(self, coodinates):
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


    def read_highways(self):
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
                result[int(way_id)-1] = coordinates_transform(coordinates)
                # result.append(v)
                # print(way_id, description, coordinates) #les tres variables són strings

    return result


    #posar un try except per si hi ha un error com l'altre dia???


    def read_congestions(self):
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


    "receives the name of a location and it returns its nearest node of the graph"
    
    
    def from_location_to_node(self, place):
        place = place + " Barcelona Catalonia"  # només amb Barcelona ja funciona, però per assegurar
        location = osmnx.geocoder.geocode(place)  # és una tupla
        print((location[1], location[0]))
        node = osmnx.distance.nearest_nodes(self.digraph, location[1], location[0])
        print(self.digraph.nodes[node])


    def itime(self):
        comparar_coordenades_prova(self.graph, self.digraph)
        for node1, info1 in self.graph.nodes.items():
            # print(node1, info1) #type(info1) = dictionary, list(info1) et diu les keys que té
            # print(graph[node1])
            # print(info1)
            # for each adjacent node and its information...
            for node2, edge in self.graph.adj[node1].items():
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
    
                #print('    ', node2)
                # print(edge)
                # print('        ', list(edge[0])) #imprimeix tots els atributs dels edges
                # print(list(graph.edges[node1, node2, 0])) #fa el mateix que la línia de sobre


    def _add_traffic_data(self, route, traffic_now):
        last_node = -1
        for node in route:
            if last_node != -1:
                self.graph.edges[last_node, node, 0]["congestion"] = max(
                    self.graph.edges[last_node, node, 0]["congestion"], traffic_now)
                self.digraph.edges[last_node, node]["congestion"] = max(
                    self.digraph.edges[last_node, node]["congestion"], traffic_now)
            last_node = node


    def _afegeix_tram(self, routes, node1, node2, traffic_now):
        try:
            route1 = osmnx.shortest_path(self.digraph, node1, node2)
            route2 = osmnx.shortest_path(self.digraph, node2, node1)
            routes.append(route1)
            self._add_traffic_data(route1, traffic_now)
            self._add_traffic_data(route2, traffic_now)
            routes.append(route2)
        except:
            pass


    def comparar_coordenades_prova(self):
    
        congestions = self.read_congestions()
        highways = self.read_highways()
        # print(list(graph.degree)) #print(list(graph.nodes)) //nodes o edges
        networkx.set_edge_attributes(self.graph, 0, "congestion")
        networkx.set_edge_attributes(self.digraph, 0, "congestion")
    
        routes = []  # Vector amb els trams de la via pública
        for i in range(534):
            v = highways[i]
            c = congestions[i]
            if len(v) != 0 and len(c) != 0:
                node1 = osmnx.distance.nearest_nodes(self.digraph, v[0][0], v[0][1])
                node2 = osmnx.distance.nearest_nodes(self.digraph, v[-1][0], v[-1][1])
                traffic_now = int(c[-3])
                traffic_later = int(c[-1])
                self._afegeix_tram(routes, node1, node2, traffic_now)
    
        # ec = osmnx.plot.get_edge_colors_by_attr(graph, "congestion", cmap="plasma")
        # osmnx.plot_graph(graph, edge_color=ec, edge_linewidth=2, node_size=0, bgcolor="#ffffff")


# Data
PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

# Code
bcn_map = geo_graph(PLACE, GRAPH_FILENAME, HIGHWAYS_URL, CONGESTIONS_URL)

