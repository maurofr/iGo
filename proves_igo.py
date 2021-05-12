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

PLACE = 'Barcelona, Catalonia'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

Highway = collections.namedtuple('Highway', 'tram') # Tram
Congestion = collections.namedtuple('Congestion', 'tram')

#we download the and save the graph(map)
def download_and_save_graph():
    graph = osmnx.graph_from_place(PLACE, network_type = 'drive', simplify = True)
    digraph = osmnx.utils_graph.get_digraph(graph, weight = 'length')
    with open(GRAPH_FILENAME, 'wb') as file:
        pickle.dump([graph, digraph], file)


def load_graph():
    with open(GRAPH_FILENAME, 'rb') as file:
        graph, digraph = pickle.load(file)
    return graph, digraph


# for each node and its information...
def print_graph():
    graph, digraph = load_graph()
    #print(list(graph.degree)) #print(list(graph.nodes)) //nodes o edges

    for node1, info1 in digraph.nodes.items():
        #print(node1, info1) #type(info1) = dictionary, list(info1) et diu les keys que té
        print(digraph[node1])
        print(info1)
        """
        # for each adjacent node and its information...
        for node2, edge in graph.adj[node1].items():
            print('    ', node2)
            print('        ', edge) #type(edge) = dictionary
        """

    #osmnx.plot_graph(graph)
def coordinates_transform(coordinates):
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


def read_highways():
    with urllib.request.urlopen(HIGHWAYS_URL) as response:
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
            #result.append(v)
            #print(way_id, description, coordinates) #les tres variables són strings

    return result

def read_congestions():
    with urllib.request.urlopen(CONGESTIONS_URL) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter=',', quotechar='"')
        #next(reader)  # ignore first line with description   en aquest cas la primera linia no s'ha d'ignorar
        result = []
        for line in reader:
            way_id = line
            result.append(way_id[0])
            #print(way_id[0]) #way_id és de tipus list de mida 1. way_id[0] és un string

    return result

def comparar_coordenades_prova():
    #congestions
    congestions = read_congestions()

    #highways
    highways = read_highways()

    graph, digraph = load_graph()
    #print(list(graph.degree)) #print(list(graph.nodes)) //nodes o edges

    routes = []
    # modificar perq fagi tot i modular-ho
    for v in highways:
        n = len(v)
        if n != 0:
            node1 = osmnx.distance.nearest_nodes(digraph, v[0][0], v[0][1])
            node2 = osmnx.distance.nearest_nodes(digraph, v[n-1][0], v[n-1][1])
        try:
            route1 = osmnx.shortest_path(digraph, node1, node2)
            route2 = osmnx.shortest_path(digraph, node2, node1)
            for node in route1:
                # asldaslkdjaslkdjasdlkajsd
            routes.append(route1)
            routes.append(route2)
        except:
            pass

    #for i in range(len(congestions)):
    #    l = len[congestions[i]]
    #    congestions[i][l-1]

    #osmnx.plot_graph_routes(graph, routes, route_linewidth=6, node_size=0, bgcolor='k')

comparar_coordenades_prova()
#print_graph()
#graph, digraph = load_graph()
#highways = read_highways()
#congestions = read_congestions()

#route1 = osmnx.shortest_path(digraph, 390227138, 687897113)
#node1 = osmnx.distance.nearest_nodes(graph, 2.206062333803802, 41.44356616311283)
#node2 = osmnx.distance.nearest_nodes(graph, 2.201961946861377, 41.44804289389951)
#node3 = osmnx.distance.nearest_nodes(graph, 2.200663088952131, 41.44881362403847)
#node4 = osmnx.distance.nearest_nodes(graph, 2.197777924171125, 41.44949306786887)
#node5 = osmnx.distance.nearest_nodes(graph, 2.196633557528038, 41.44990657344401)

#diag1 = osmnx.distance.nearest_nodes(digraph, 2.167816301234855,41.37498443097444)
#diag2 = osmnx.distance.nearest_nodes(digraph, 2.175962748986153,41.37437372698415)

#route1 = osmnx.shortest_path(digraph, diag2, diag1)
#route2 = osmnx.shortest_path(digraph, diag1, diag2)
#route1 = osmnx.shortest_path(graph, node1,node3)
#route2 = osmnx.shortest_path(graph, node2, node3)
#route3 = osmnx.shortest_path(graph, node3, node4)
#route4 = osmnx.shortest_path(graph, node4, node5)
#osmnx.plot_graph_route(graph, route1, route_linewidth=6, node_size=0, bgcolor='k')
