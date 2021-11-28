"""
Calculate demand by hour of day and time bin

Create visualization for average distance between top travel nodes.
"""
import folium
import pandas as pd
import numpy as np
import geopandas as gpd

import sqlalchemy as sa
import geoalchemy2 as ga
from pyproj import Proj

from hcme.metrics import metric

from hcme.db import models, engine
from hcme.crs import UTM10

from dataclasses import dataclass

Trip = models.Trip
Person = models.Person
Household = models.Household

Location = models.Location
Destination = sa.orm.aliased(Location)
Home = sa.orm.aliased(Location)
Origin = sa.orm.aliased(Location)


METERS_TO_MILE = 0.000621371  # 1 meter = 0.000621371 miles

star = (
    sa.select(
        Trip,
        Destination.city.label("destination_city"),
        Origin.city.label("origin_city"),
        Home.city.label("home_city"),
        ga.func.ST_MakeLine(Destination.coordinates, Origin.coordinates).label(
            "linear_distance"
        ),
    )
    .join(Destination, Trip.destination_location_id == Destination.id)
    .join(Origin, Trip.origin_location_id == Origin.id)
    .join(Person, Trip.person_id == Person.id)
    .join(Household, Person.household_id == Household.id)
    .join(Home, Household.location_id == Home.id)
)


@dataclass
class DemandMatrix:

    time_bins = {
        "pre-dawn": [*range(3, 6)],
        "morning": [*range(6, 11)],
        "noon": [*range(11, 16)],
        "evening": [*range(16, 22)],
        "night": [*range(0, 3), *range(22, 25)],
    }

    threshold: int = None
    top_n: int = 10

    def __post_init__(self):
        # Create dataframe with grain of hour of day, start location, end location
        gdf = gpd.read_postgis(star, con=engine, geom_col="linear_distance")

        # Define travel distance
        gdf["miles"] = gdf["linear_distance"].to_crs(UTM10.crs).length * METERS_TO_MILE

        gdf["hour"] = np.floor(gdf["departure"].dt.total_seconds() / 60 / 60).astype(
            int
        )

        for label, rng in self.time_bins.items():
            metric(
                self._calculate(gdf, rng, self.threshold, self.top_n),
            )
        self.data = gdf

    def _calculate(gdf, hours, threshold=None, top_n=None):
        # Filter out all destinations that do not have at least `threshold` trips
        mask = gdf["hour"].isin(hours)
        gdf = gdf[mask].copy()
        trip_counts = (
            gdf.groupby("destination_city")["id"].count().sort_values(ascending=False)
        )
        if threshold:
            trip_counts = trip_counts[trip_counts > threshold]
        cities = trip_counts.index.tolist()
        if top_n:
            cities = cities[:top_n]
        cities = sorted(cities)

        # Only include cities meeting criteria
        mask = gdf["destination_city"].isin(cities)
        gdf = gdf[mask].copy()

        # Now aggregate!
        pivot = (
            gdf.groupby(["origin_city", "destination_city"], as_index=False)["id"]
            .agg({"trips": "count"})
            .pivot(index="origin_city", columns="destination_city", values="trips")
        )
        return pivot


@metric(domain="demand")
def am_trip_summary():
    """City origin/destination trip matrix by AM trips (i.e. trips before Noon)"""
