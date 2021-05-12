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

    for node1, info1 in graph.nodes.items():
        print(node1, info1) #type(info1) = dictionary, list(info1) et diu les keys que té

        # for each adjacent node and its information...
        for node2, edge in graph.adj[node1].items():
            print('    ', node2)
            print('        ', edge) #type(edge) = dictionary

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
        result = []
        for line in reader:
            v = []
            way_id, description, coordinates = line
            v.append(way_id)
            v.append(description)
            v.append(coordinates)
            result.append(coordinates_transform(coordinates))
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

    for v in highways:
        for c in v:
            X0 = c[0]
            Y0 = c[1]
            node = osmnx.distance.nearest_nodes(digraph, X0, Y0)


comparar_coordenades_prova()
