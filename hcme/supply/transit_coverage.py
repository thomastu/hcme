"""Tools for computing transit coverage.
"""
from functools import reduce
from typing import Tuple

import geopy
import networkx as nx
import osmnx as ox
from pyrosm import OSM

from hcme import config

# Create network graph

fp = str(config.input_dir / "humboldt.osm.pbf")

osm = OSM(fp)

nodes, edges = osm.get_network(nodes=True, network_type="walking")

nodes["x"] = nodes["lon"]
nodes["y"] = nodes["lat"]

graph = osm.to_graph(nodes, edges, graph_type="networkx")

lngs = edges.head().centroid.map(lambda x: x.coords[0][0])
lats = edges.head().centroid.map(lambda x: x.coords[0][1])

# # the lat, lng at the spatial center of the graph
# lng, lat = edges.unary_union.centroid.coords[0]

# # Pick which point to calculate distances from
# center_point = lat, lng

# center_node = ox.distance.nearest_nodes(graph, lng, lat)

# nearest_nodes = ox.distance.nearest_nodes(graph, lngs, lats, method='balltree')
# nearest_edge = ox.distance.nearest_edges(graph, center_point)
# nearest_edges = ox.distance.nearest_edges(graph, lngs, lats)

# Find shortest path by distance between these nodes

orig = list(graph)[0]
dest = list(graph)[-1]

# Compute route
route = nx.shortest_path(graph, orig, dest, weight="length")

# Plot route
fig, ax = ox.plot_graph_route(graph, route, route_linewidth=6, node_size=0, bgcolor="k")


def route_to_nearest_stop(o_coords: Tuple, d_coords: Tuple, graph: nx.DiGraph):
    """Plot the shortest route between the nearest nodes on the ``graph`` between two points.

    Args:
        o_coords (Tuple): (x, y) tuple for origin coordinates.
        d_coords (Tuple): (x, y) tuple for destination coordinates
        graph (nx.DiGraph): graph to inspect

    Returns:
        [type]: [description]
    """
    # Find the nearest node to the origin coordinates

    o_node = ox.nearest_nodes(graph, *o_coords)
    d_node = ox.nearest_nodes(graph, *d_coords)

    def _heuristic(o, d):
        o_node, d_node = graph.nodes[o], graph.nodes[d]
        origin = (o_node["y"], o_node["x"])
        dest = (d_node["y"], d_node["x"])
        return geopy.distance.distance(origin, dest).meters

    route = ox.distance.shortest_path(graph, o_node, d_node, weight="length", cpus=None)
    return route


def calculate_route_length(route: list, graph: nx.DiGraph):
    u = route[0]
    dist = 0
    for v in route[1:]:
        dist += graph[u, v]["length"]
        u = v
    return dist


# Plot random trip from events:
from hcme.crs import UTM10, WGS84

o_coords = (-124.08909939596784, 40.86928065084382)
d_coords = (-124.07695930632568, 40.87426729048089)
