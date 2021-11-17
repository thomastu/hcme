from lxml import etree
from hcme.beamio.factory import TemplateLoader, template_namespaces

data = {
    "population": [
        {
            "id": 1,
            "attributes": [
                {"name": "age", "type": "java.lang.Integer", "value": 28},
                {"name": "sex", "type": "java.lang.String", "value": "M"},
            ],
            "excluded_modes": ["car"],
            "rank": 0,
            "plan": [
                {
                    "type": "Home",
                    "y": "4524819.50223867",
                    "x": "408202.0350928387",
                    "end_time": "9:00:00",
                },
                {
                    "type": "School",
                    "y": "4525378.715445407",
                    "x": "409050.5632430612",
                    "end_time": "17:00:00",
                    "mode": "walk",
                },
                {
                    "type": "Home",
                    "y": "4524819.50223867",
                    "x": "408202.0350928387",
                    "mode": "walk",
                },
            ],
        },
        {
            "id": 2,
            "attributes": [
                {"name": "age", "type": "java.lang.Integer", "value": 25},
                {"name": "sex", "type": "java.lang.String", "value": "F"},
            ],
            "rank": 1,
            "plan": [
                {
                    "type": "Home",
                    "y": "4524819.50223867",
                    "x": "408202.0350928387",
                    "end_time": "9:00:00",
                },
                {
                    "type": "Other",
                    "y": "4524671.101160721",
                    "x": "408411.3689155844",
                    "end_time": "12:00:00",
                    "mode": "walk",
                },
                {
                    "type": "Home",
                    "y": "4524819.50223867",
                    "x": "408202.0350928387",
                    "mode": "walk",
                },
            ],
        },
    ],
    "households": [
        {
            "id": 1,
            "members": [1, 2],
            "income": 100000,
            "homecoordx": 408202.0350928387,
            "homecoordy": 4524819.50223867,
        }
    ],
}


def test_render_population():
    """Check for expected attributes against pre-canned data in population template."""
    output = TemplateLoader("population", data).render()
    tree = etree.fromstring(output.encode("utf-8"))
    assert len(tree.xpath("//person")) == len(data["population"])
    for i, pop in enumerate(data["population"], 1):
        assert len(tree.xpath(f"//person[{i}]/plan/activity")) == len(pop["plan"])
        assert len(tree.xpath(f"//person[{i}]/attributes/attribute")) == len(
            pop["attributes"]
        )


def test_render_population_attributes():
    output = TemplateLoader("population_attributes", data).render()
    tree = etree.fromstring(output.encode("utf-8"))
    for person in data["population"]:
        person_id = person["id"]
        assert tree.xpath(f"//object[@id='{person_id}']")


def test_render_household():
    """Check for expected attributes against pre-canned data in household template."""
    output = TemplateLoader("households", data).render()
    ns = template_namespaces["households"]
    tree = etree.fromstring(output.encode("utf-8"))
    assert len(tree.xpath("//default:household", namespaces=ns)) == len(
        data["households"]
    )
    for i, household in enumerate(data["households"], 1):
        assert len(
            tree.xpath(
                f"//default:household[{i}]/default:members/default:personId",
                namespaces=ns,
            )
        ) == len(household["members"])
        assert tree.xpath(
            f"//default:household[{i}]/default:income/text()", namespaces=ns
        )[0] == str(household["income"])


def test_render_household_attributes():
    """Check for expected attributes against pre-canned data in household attributes template."""
    output = TemplateLoader("household_attributes", data).render()
    tree = etree.fromstring(output.encode("utf-8"))
    assert len(tree.xpath("//object")) == len(data["households"])
    for i, household in enumerate(data["households"], 1):
        assert tree.xpath(f"//object[{i}]/attribute[@name='homecoordx']/text()")[
            0
        ] == str(household["homecoordx"])
        assert tree.xpath(f"//object[{i}]/attribute[@name='homecoordy']/text()")[
            0
        ] == str(household["homecoordy"])
