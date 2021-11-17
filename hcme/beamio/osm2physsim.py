# Converts an OSM file to a physsim-network.xml input
import pandas as pd

from lxml import etree
from pyrosm import OSM


# Miles per hour to meters per second
mph_to_mps = 0.44704


def main(fp: str, from_crs: str = "EPSG:4326", to_crs: str = "EPSG:26910"):
    """
    Convert an open street maps pbf file (.osm.pbf) to a matsim network file.

    Args:
        fp (str): Path or pathlike to the osm file.
    """
    osm = OSM(fp)

    # Read the OSM file into a Geopandas DataFrame
    nodes, links = osm.get_network(nodes=True, network_type="all")

    # Convert geometry to target CRS
    nodes = nodes.set_crs(from_crs).to_crs(to_crs)

    # Create nodes dictionary
    nodes["x"] = nodes.geometry.x
    nodes["y"] = nodes.geometry.y

    nodes = nodes[["id", "x", "y"]].to_dict(orient="records")

    links = links[["id", "u", "v", "length", "freespeed", "highway"]]
