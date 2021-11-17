"""
Modify a population file.

A population file follows the following schema:

<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">

<population>

    <person id="{person-id}">
        <attributes>
            <attribute name="{attribute-name}" class="{attribute-type}">{value}</attribute>
        </attributes>

        <plan selected="yes">
            <activity type="{activity-type}" x="{start-coordinate-x}" y="{start-coordinate-y}" end_time="{end-time}">
            </activity>
        </plan>

    </person>

</population>

"""
from lxml import etree
from pyproj import Transformer

from hcme.beamio.factory import TemplateLoader


def create_agent():
    pass


# TemplateLoader("population", data).render()
