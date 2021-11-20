"""
Factories are responsible for building templated inputs.

Factory outputs can be used to create test fixtures, or ready-to-use BEAM input files.
"""

from dataclasses import dataclass
from jinja2 import Environment, PackageLoader, select_autoescape

from .constants import InputRegistry as INPUTS

template_env = Environment(
    loader=PackageLoader("hcme.beam", "templates"),
    autoescape=select_autoescape(["xml"]),
)


template_registry = {
    INPUTS.HOUSEHOLDS.value: "households.xml.j2",
    INPUTS.POPULATION.value: "population.xml.j2",
    INPUTS.POPULATIONATTRIBUTES.value: "population_attributes.xml.j2",
    INPUTS.HOUSEHOLDATTRIBUTES.value: "household_attributes.xml.j2",
    INPUTS.NETWORK.value: "physsim-network.xml.j2",
}

DEFAULT_NS = "default"

template_namespaces = {
    INPUTS.HOUSEHOLDS.value: {
        DEFAULT_NS: "http://www.matsim.org/files/dtd",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    },
    INPUTS.POPULATION.value: {},
}


@dataclass
class TemplateLoader:

    template: str
    data: dict

    def __post_init__(self):
        self.template = template_env.get_template(template_registry.get(self.template))

    def write(self, output: str = None):
        stream = self.template.stream(**self.data)
        stream.dump(output)

    def render(self, output: str = None):
        document = self.template.render(**self.data)
        return document
