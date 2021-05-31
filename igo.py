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

Highway = collections.namedtuple('Highway', 'tram')
Congestion = collections.namedtuple('Congestion', 'tram')


class iGraph():

    """
    The iGraph class saves a an intelligent graph of a place. It is now designed
    for Barcelona as it retrieves its live traffic data so that the graph can be
    used to find the optimal between two places.
    """

    # Init methods:
    def __init__(self, place, file, highways_url, congestions_url):
        """
        PRE: - place: the name of a city (right now it must be Barcelona) (Str)
             - file: file in which data will be saved (Str)
             - highways_url: the url of the database with Barcelona's highways (Str)
             - congestions_url: the url of the live traffic data of the highways (Str)
        ------------------------------------------------------------------------
        POST: The graph of the place is imported and saved on a file so that it
              can be loaded for future iGraphs.
              All the PRE information is saved in private variables.
              New attributes are added to the graph with value '0' such as
              "congestion" and "itime".
              The highways are computed and stored in a private matrix containing
              its nodes.
        """
        # We will not compute bearings as they are not used in the current implementation
        self.bearings = False

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
        self._highways_nodes = []  # Vector amb els trams de la via pública
        self._add_attributes()
        self._define_highways_nodes()

    def _add_edge_bearings_digraph(self):
        """
        PRE: - A newtorkx.digraph
        ------------------------------------------------------------------------
        POST: A new attribute is added to each edge of the graph containing the
              bearing of the edge rounded to 1 decimal number.
        """
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
        It adds all the necessary attributes to the edges. By default bearings
        are not added as they are not used for itime (live shortest-path-finding).

        PRE: - self._bearings: tells if the bearing atribute will be added (Bool)
             - self._graph: the networkx.mulitgraph of Barcelona
             - self.digraph: the networkx.digraph of Barcelona
        ------------------------------------------------------------------------
        POST: New attributes to the multigraph:
              - "congestion" for every edge, initialized as 0
              - "bearing" if bearings is True
              New attributes to the digraph:
              - "congestion" for every edge, initialized as 0
              - "itime" for every edge, initialized as 0
              - "bearing" if bearings is True
        """
        networkx.set_edge_attributes(self._graph, 0, "  ")
        networkx.set_edge_attributes(self.digraph, 0, "itime")
        networkx.set_edge_attributes(self.digraph, 0, "congestion")
        if self.bearings:
            networkx.set_edge_attributes(self._graph, 0, "bearing")  # Edges without a bearing are laces
            networkx.set_edge_attributes(self.digraph, 0, "bearing")
            osmnx.bearing.add_edge_bearings(self._graph)
            self._add_edge_bearings_digraph()  # Osmnx bearing function is only for multigraphs

    def _add_highway(self, node1, node2):
        """
        Finds the path between the two extremity nodes of the highway in both
        directions. The path is computed as the shortes path lentgh-wise.

        PRE: - node1, node2: the two nodes at the extremities of the highway
             - self.digraph: the digraph is used to find the shortest path
             - self._highways_nodes: with i-1 vectors (Matrix)
        ------------------------------------------------------------------------
        POST: If the nodes are connected in both directions, the paths are appended
              to self._highways_nodes in a single vector.
              Else an empty vector indicating that there is no highway for key
              "i" is appended.
        """
        try:
            route1 = osmnx.shortest_path(self.digraph, node1, node2)
            route2 = osmnx.shortest_path(self.digraph, node2, node1)
            self._highways_nodes.append([route1, route2])
        except:
            self._highways_nodes.append([])

    def _define_highways_nodes(self):
        """
        We save the highways in a graph-friendly format in order to be able to
        update live traffic data for each highway efficiently.

        PRE: - self._highways_url: the url to access Barcelona's highways (Str)
             - self._highways_nodes: empty array
             - self._highways: data from Barcelona's highways (Vector)
        ------------------------------------------------------------------------
        POST: self._highways[i] contains two paths of nodes, one for each direction,
              of the highway with key "i" (in Barcelona's highways database).
              self._highways[i] can be empty due to some highways being empty and
              others out of the limits of our graph.
        """
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
        """
        Detailed information of the digraph is displayed in a human-friendly way.
        """
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
        """
        It returns the __str__() output. For more information see its documentation.
        """
        return self.__str__()

    def print_graph(self):
        """
        It plots the graph of the place.

        PRE: self._graph, the multigraph ad the digraph is not supported by the
             plotting library.
        ------------------------------------------------------------------------
        POST: The graph is plotted on a display. If no display is found it is
              saved as "graph_plot.png".
        """
        try:
            osmnx.plot_graph(self._graph)
        except:
            print("There is no display to plot the graph. Saved as graph_plot.png")
            osmnx.plot_graph(self._graph, show=False, save=True, filepath='graph_plot.png')

    def print_congestions(self):
        """
        It plots a colormap of the edge's congestion.
        The colormap is plotted on a display. If no display is found it is
        saved as "congestions_plot.png".
        """
        try:
            ec = osmnx.plot.get_edge_colors_by_attr(self._graph, "congestion", cmap="YlOrRd")
            osmnx.plot_graph(self._graph, edge_color=ec, edge_linewidth=2, node_size=0)
        except:
            print("There is no display to plot the graph. Saved as congestions_plot.png")
            osmnx.plot_graph(self._graph, edge_color=ec, edge_linewidth=2, node_size=0,
                             show=False, save=True, filepath='congestions_plot.png')

    def print_bearings(self):
        """
        It plots a colormap of the edge's bearings.

        PRE: - self._bearings: indicates if bearings are considered (Bool)
        -----------------------------------------------------------------------------
        POST: The colormap is plotted on a display. If no display is found it is
              saved as "bearings_plot.png".
        """
        if self.bearings:
            cols = osmnx.plot.get_edge_colors_by_attr(self._graph, "bearing", num_bins=360, cmap="YlOrRd")
            try:
                osmnx.plot_graph(self._graph, edge_color=cols, edge_linewidth=2, node_size=0)
            except:
                print("There is no display to plot the graph. Saved as bearings_plot.png")
                osmnx.plot_graph(self._graph, edge_color=cols, edge_linewidth=2, node_size=0,
                                 show=False, save=True, filepath='bearings_plot.png')

    def print_path(self, path):
        """
        Plots the map of the city centered in the region, with the path visible on it.

        PRE: - path: a collection of nodes (Vector)
        -------------------------------------------------------------------------------
        POST: It calculates the minimum region in which the path is visible. Then,
              it is plotted on a display. If no display is found it is saved as
              "path_plot.png".
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
        try:
            osmnx.plot_graph_route(self._graph, route, route_color='r', route_linewidth=3,
                                   route_alpha=1, node_size=0, bgcolor='k', bbox=bbox)
        except:
            print("There is no display to plot the graph. Saved as path_plot.png")
            osmnx.plot_graph(self._graph, route, route_color='r', route_linewidth=3,
                             route_alpha=1, node_size=0, bgcolor='k', bbox=bbox,
                             show=False, save=True, filepath='bearings_plot.png')

    def _print_progress_bar(self, iteration, total):
        """
        Prints a progress bar for the iterations of a loop.

        PRE: - iteration: current iteration (Int)
             - total: total iterations (Int)
        ------------------------------------------------------------------------
        POST: Prints a progress bar and the percentage of the loop completed.
        """
        fill = '█'
        percent = ("{0:." + str(1) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(100 * iteration // total)
        bar = fill * filledLength + '-' * (100 - filledLength)
        print(f'\r |{bar}| {percent}% ', end="\r")

    # Live data reading and processing methods:
    def _coordinates_transform(self, coordinates):
        """
        It transforms a string of coordinates into a pair of floats.

        PRE: - coordinates: the coordinates separated with a comma (Str)
        ------------------------------------------------------------------------
        POST: returns a vector with two elements, latitude and longitude as floats
        """
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
        """
        Reads the data from the database of Barcelona's highways.

        PRE: - self._highways_url: the url from which to extract the data (Str)
        ------------------------------------------------------------------------
        POST: Returns a vector in which the position "i" has the data of the
              i-th highway (highway with hey "i")
        """
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
        """
        Reads the data from the database containing the congestion of Barcelona's
        highways.

        PRE: - self._congestions_url: the url from which to extract the data (Str)
        --------------------------------------------------------------------------
        POST: Returns a vector in which the position "i" has the congestion of the
              i-th highway (highway with hey "i").
        """
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

    def _update_traffic_data(self, traffic_now, highway):
        """
        Auxiliary function to get_traffic. It updates the congestion of a highway.

        PRE: - highway: highway's paths of nodes (Vector)
             - traffic_now: current value of the highway's congestion (Int)
        -------------------------------------------------------------------------
        POST: For each edge in each route the "congestion" attribute is equal to
              traffic_now.
        """
        for route in highway:
            last_node = -1
            for node in route:
                if last_node != -1:
                    self._graph.edges[last_node, node, 0]["congestion"] = traffic_now
                    self.digraph.edges[last_node, node]["congestion"] = traffic_now
                last_node = node

    def get_traffic(self):
        """
        Overwrites current traffic information with live congestion data of
        Barcelona's highways.

        PRE: self.digraph, self._graph
        ------------------------------------------------------------------------
        POST: Values are saved in each edge's "congestion" attribute in both graphs.
        """
        congestions = self._read_congestions()

        for i in range(534):
            c = congestions[i]
            if len(c) != 0:
                traffic_now = int(c[-3])
                self._update_traffic_data(traffic_now, self._highways_nodes[i])

    # Other methods:
    def from_location_to_node(self, lat, lon):
        """
        Receives the coordinates of a location and it returns its nearest node
        on the graph.

        PRE: - lat, lon: latitude and longitude values (Float)
        ------------------------------------------------------------------------
        POST: Returns the nearest node in the graph.
        """
        node = osmnx.distance.nearest_nodes(self.digraph, lon, lat)  # lon = 2. i lat = 41.
        return node

    def _itime(self):
        """
        The 'itime' attribute is calculated using the speed, length and congestions
        of a street (edge). It contains the expected time in seconds to go from the
        start to the end of the street.
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
        It calculates the shortest path between two nodes taking into account the
        'itime' attribute. It also calculates the time needed to complete the path.

        PRE: - origin_lat, origin_lon: latitude and longitude of the origin node (Float)
             - destination_lat, destination_lon: same for the destination node (Float)
        --------------------------------------------------------------------------------
        POST: Returns the path with each node and its information and the total
              travel time in seconds.
        """
        self._itime()
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
