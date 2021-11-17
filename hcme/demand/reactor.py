"""
Build and create BEAM input plans
"""
import datetime
from typing import Dict, Iterable

import geoalchemy2 as ga
import pandas as pd
import sqlalchemy as sa

from hcme.beamio import population
from hcme.beamio.factory import TemplateLoader, template_namespaces
from hcme.db import Session, models
from pyproj import Proj
from tqdm import tqdm


UTM10 = Proj(proj="utm", zone=10, ellps="WGS84")


def build_plan(
    coordinates: ga.elements.WKBElement,
    depart: datetime.timedelta = None,
    trip_type: str = "Other",
):
    """Build a single plan for one person and convert to expected BEAM coordinates."""
    point = ga.shape.to_shape(coordinates)
    x, y = UTM10(point.x, point.y)
    data = {
        "type": trip_type,
        "x": x,
        "y": y,
    }
    if depart:
        # Note that str(timedelta) -> "HH:MM:SS.ss"
        data["end_time"] = str(depart).split(".")[0]
    return data


def generate_person_plans(pct_vehicle_ownership: float) -> Iterable[Dict]:
    """Go through each person and their trips"""

    session = Session()
    for _q in tqdm(session.execute(sa.select(models.Person))):
        person = _q.Person
        # Get person trips
        destinations = sa.orm.aliased(models.Location)
        origins = sa.orm.aliased(models.Location)
        query = (
            sa.select(
                models.Trip,
                sa.func.bool(
                    models.Household.location_id == models.Trip.destination_location_id
                ).label("is_destination_home"),
                sa.func.bool(
                    models.Household.location_id == models.Trip.origin_location_id
                ).label("is_origin_home"),
                destinations.coordinates.label("destination"),
                origins.coordinates.label("origin"),
            )
            .join(destinations, models.Trip.destination_location_id == destinations.id)
            .join(origins, models.Trip.origin_location_id == origins.id)
            .join(models.Person, models.Trip.person_id == models.Person.id)
            .join(models.Household, models.Person.household_id == models.Household.id)
            .where(models.Trip.person_id == person.id)
            .order_by(models.Trip.trip_leg)
        )

        trips = session.execute(query)

        plan = []

        for trip in trips:
            trip_type = "Home" if trip.is_origin_home else "Other"
            plan.append(
                build_plan(trip.origin, trip.Trip.departure, trip_type=trip_type)
            )

        # Include final leg as plan without end time.
        trip_type = "Home" if trip.is_destination_home else "Other"
        plan.append(build_plan(trip.destination, trip_type=trip_type))

        yield {"id": person.id, "plan": plan}

def 


def build_travel_diary(pct_vehicle_ownership: float, output_path: str) -> None:
    """Build a travel diary"""
    population = generate_person_plans(pct_vehicle_ownership)
    population_loader = TemplateLoader("population", {"population": population}).write(
        output_path
    )
    household_loader = TemplateLoader()
