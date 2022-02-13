"""Load the beam network file to re-construct events.
"""
from pathlib import Path

from geoalchemy2 import WKTElement
from loguru import logger
from lxml import etree
from pyproj import Transformer
from tqdm import tqdm

from hcme.config import beam_conf
from hcme.crs import UTM10, WGS84
from hcme.db import Session, models
from hcme.db.io import make_loader

network_file = Path(beam_conf).parent / "r5/physsim-network.xml"

# Import all nodes first
NodeLoader = make_loader(models.Node, grain=["id"])
LinkLoader = make_loader(models.Link, grain=["from_node_id", "to_node_id"])

utm10_to_wgs84 = Transformer.from_crs(UTM10.crs, WGS84.crs)

if __name__ == "__main__":

    network = etree.parse(str(network_file))
    nodes = network.xpath("//nodes/node")
    links = network.xpath("//links/link")

    session = Session()

    node_loader = NodeLoader(session, batch_size=10000)
    link_loader = LinkLoader(session, batch_size=10000)

    for node in tqdm(nodes):

        # First create a shapely coordinate and convert from UTM10 to EPSG:4326
        node_id = node.attrib["id"]
        x, y = utm10_to_wgs84.transform(node.attrib["x"], node.attrib["y"])
        coordinates = WKTElement(f"POINT({x} {y})", srid=4326)
        node_loader.stream({"id": node_id, "coordinates": coordinates})

    node_loader.flush()
    cache = set()
    for link in tqdm(links):
        link_id = int(link.attrib["id"])
        from_node_id = int(link.attrib["from"])
        to_node_id = int(link.attrib["to"])
        key = f"{from_node_id}:{to_node_id}"

        if key in cache:
            logger.info(
                "Duplicate link detected : {from_node_id}:{to_node_id}",
                from_node_id=from_node_id,
                to_node_id=to_node_id,
            )
            continue

        cache.add(key)
        link_loader.stream(
            {"id": link_id, "from_node_id": from_node_id, "to_node_id": to_node_id}
        )

    link_loader.flush()
