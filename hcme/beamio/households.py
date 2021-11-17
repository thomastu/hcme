from lxml import etree


NS = "default"

namespaces = {
    NS: "http://www.matsim.org/files/dtd",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

tree = etree.parse("/path/to/file.xml")


from dataclasses import dataclass
