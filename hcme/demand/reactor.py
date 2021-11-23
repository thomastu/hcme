"""
Build and create BEAM input plans
"""
import csv
import datetime
from typing import Dict, Iterable

import geoalchemy2 as ga
import pandas as pd
import sqlalchemy as sa
import numpy as np


from hcme.beam.factory import TemplateLoader
from hcme.db import Session, models
from pyproj import Proj
from tqdm import tqdm

from hcme.db.models.world.census_block_demographics import CensusBlockEconomics

from hcme.config import artifacts

from loguru import logger

UTM10 = Proj(proj="utm", zone=10, ellps="WGS84")


destinations = sa.orm.aliased(models.Location)
origins = sa.orm.aliased(models.Location)

household_locations = sa.orm.aliased(models.Location)

cities = [
    "Korbel",
    # "Mckinleyville",
    "Redway",
    "Garberville",
    "Pepperwood",
    "Redcrest",
    "Hoopa",
    "Willow Creek",
    # "Cutten",
    "Whitethorn",
    # "Bayside",
    # "Trinidad",
    "Forks Of Salmon",
    # "Manila",
    "McCann",
    # "Fortuna",
    "Piercy",
    "Waddington",
    "Myers Flat",
    "Port Kenyon",
    "Phillipsville",
    # "Arcata",
    "Scotia",
    "Ettersburg",
    "Carlotta",
    "Fields Landing",
    "Klamath Glen",
    "Somes Bar",
    "Salyer",
    "Miranda",
    "Honeydew",
    # "Rio Dell",
    # "McKinleyville",
    "Kneeland",
    "Loleta",
    "Aptos",
    "Hyampom",
    "Weott",
    "Alderpoint",
    "Whitlow",
    "Stafford",
    # "Eureka",
    # "Blue Lake",
    "Orleans",
    "Shively",
    "Pecwan",
    "Burnt Ranch",
    "Blocksburg",
    "Zenia",
    "Mad River",
    "Klamath",
    "Benbow",
    "Westhaven",
    "Orick",
    "Bridgeville",
    # "Ferndale",
    # "Samoa",
    "Hydesville",
    "Petrolia",
]

geatm_trips = (
    sa.select(household_locations.id)
    .join(models.Household, household_locations.id == models.Household.location_id)
    .join(models.Person, models.Household.id == models.Person.household_id)
    .join(models.Trip, models.Trip.person_id == models.Person.id)
    .join(destinations, models.Trip.destination_location_id == destinations.id)
    .join(origins, models.Trip.origin_location_id == origins.id)
    .where(sa.not_(sa.and_(origins.city.in_(cities), destinations.city.in_(cities))))
    .distinct()
)


where_clause = sa.and_(models.Location.id.in_(geatm_trips.subquery()))


def WKB_to_xy(wkbelement, transformer=UTM10):
    # Build a shapely point first
    point = ga.shape.to_shape(wkbelement)
    x, y = transformer(point.x, point.y)
    return x, y


def build_plan(
    coordinates: ga.elements.WKBElement,
    depart: datetime.timedelta = None,
    trip_type: str = "Other",
):
    """Build a single plan for one person and convert to expected BEAM coordinates."""
    x, y = WKB_to_xy(coordinates, transformer=UTM10)
    data = {
        "type": trip_type,
        "x": x,
        "y": y,
    }
    if depart:
        # Note that str(timedelta) -> "HH:MM:SS.ss"
        data["end_time"] = str(depart).split(".")[0]
    return data


def generate_person_plans(person_where=None) -> Iterable[Dict]:
    """Go through each person and their trips"""

    session = Session()
    query = (
        sa.select(models.Person)
        .join(models.Household, models.Person.household_id == models.Household.id)
        .join(models.Location, models.Household.location_id == models.Location.id)
        .where(where_clause)
    )
    if person_where:
        query = query.where(person_where)
    for result in tqdm(session.execute(query)):
        person = result.Person
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


def generate_households(
    pct_vehicle_ownership: float, vehicle_type="beamVilleCar"
) -> Iterable[Dict]:
    session = Session()

    q = (
        sa.select(
            models.Household,
            models.Location.census_block_geoid.label("census_block_id"),
        )
        .join(
            models.Location,
            models.Location.id == models.Household.location_id,
        )
        .where(where_clause)
        .order_by(models.Household.id)
    )

    county_median_income = 40000

    fh = artifacts.vehicles.open("w")

    vehicles_recorder = csv.writer(fh, delimiter=",")
    vehicles_recorder.writerow(["vehicleId", "vehicleTypeId", "householdId"])

    for household, census_block_id in tqdm(session.execute(q)):
        economics = pd.read_sql_query(
            sa.select(models.CensusBlockEconomics).where(
                models.CensusBlockEconomics.block_id == census_block_id
            ),
            con=session.bind.engine,
        )
        # Fix the number of vehicles per household
        np.random.seed(household.id)
        num_vehicles = np.random.binomial(
            len(household.members),
            pct_vehicle_ownership,
        )

        if not economics["pct"].sum():
            income_bracket = county_median_income
        else:
            income_bracket = economics.sample(
                1, weights="pct", random_state=household.id
            ).iloc[0]
            np.random.seed(household.id)
            income = np.random.uniform(
                income_bracket["household_income_lower_bound"],
                income_bracket["household_income_upper_bound"],
            )

        data = {
            "id": household.id,
            "members": [m.id for m in household.members],
            "vehicles": [f"{household.id}-{i}" for i in range(num_vehicles)],
            "income": income,
        }
        for vehicle in data["vehicles"]:
            vehicles_recorder.writerow([vehicle, vehicle_type, household.id])
        yield data

    fh.close()


def generate_household_attributes():

    session = Session()
    query = (
        sa.select(models.Household, models.Location.coordinates.label("coordinates"))
        .join(models.Location, models.Location.id == models.Household.location_id)
        .where(where_clause)
    )

    for (household, coordinates) in tqdm(session.execute(query)):
        x, y = WKB_to_xy(coordinates, transformer=UTM10)
        yield {"id": household.id, "homecoordx": x, "homecoordy": y}


def generate_person_attributes():

    session = Session()
    query = (
        sa.select(models.Household)
        .join(models.Location, models.Household.location_id == models.Location.id)
        .where(where_clause)
    )
    for (household,) in tqdm(session.execute(query)):
        # Order household members by id
        for i, person in enumerate(sorted(household.members, key=lambda m: m.id)):
            # TODO: Include a way of assigning excluded modes something like
            # np.random.seed(household.id)
            # np.random.choice(["walk", "bike", "drive"], p=[0.2, 0.2, 0.6])
            yield {"id": person.id, "rank": i, "excluded_modes": []}


def build_travel_diary(pct_vehicle_ownership: float) -> None:
    """Build a travel diary"""
    data = {
        "population": generate_person_plans(),
        "households": generate_households(pct_vehicle_ownership),
    }

    logger.info("Generating population plans to {f}", f=artifacts.population)
    TemplateLoader("population", data).write(str(artifacts.population))

    logger.info("Generating households to {f}", f=artifacts.households)
    TemplateLoader("households", data).write(str(artifacts.households))

    attributes = {
        "households": generate_household_attributes(),
        "population": generate_person_attributes(),
    }

    logger.info(
        "Generating household attributes to {f}", f=artifacts.population_attributes
    )
    TemplateLoader("population_attributes", attributes).write(
        str(artifacts.population_attributes)
    )

    logger.info(
        "Generating household attributes to {f}", f=artifacts.household_attributes
    )
    TemplateLoader("household_attributes", attributes).write(
        str(artifacts.household_attributes)
    )
