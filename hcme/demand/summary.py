"""
Calculate demand by hour of day and time bin

Create visualization for average distance between top travel nodes.
"""
from dataclasses import dataclass
from typing import List

import folium
import geoalchemy2 as ga
import geopandas as gpd
import numpy as np
import pandas as pd
import sqlalchemy as sa
from hcme.crs import UTM10
from hcme.db import engine, models
from hcme.metrics import metric
from pyproj import Proj

domain = "demand/destination-od-matrix"

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

    def _calculate(
        self,
        gdf: gpd.GeoDataFrame,
        hours: List,
        threshold: int = None,
        top_n: int = None,
        gb: str = "destination_city",
    ):
        """
        Calculate origin-destination matrix keeping only cities that have at least ``threshold`` trips as a destination,
        and only keeping the top ``top_n`` destination cities.
        """
        # Filter out all destinations that do not have at least `threshold` trips
        mask = gdf["hour"].isin(hours)
        gdf = gdf[mask].copy()
        trip_counts = gdf.groupby(gb)["id"].count().sort_values(ascending=False)
        if threshold:
            trip_counts = trip_counts[trip_counts > threshold]
        cities = trip_counts.index.tolist()
        if top_n:
            cities = cities[:top_n]
        cities = sorted(cities)

        # Only include cities meeting criteria
        mask = gdf[gb].isin(cities)
        gdf = gdf[mask].copy()

        # Now aggregate!
        pivot = (
            gdf.groupby(["origin_city", "destination_city"], as_index=False)["id"]
            .agg({"trips": "count"})
            .pivot(index="origin_city", columns=gb, values="trips")
        )
        # Sort columns by destination count
        cities = pivot.sum(axis=0).sort_values(ascending=False).index.tolist()
        return pivot.sort_index()[cities]

    def calculate(self, data, time_bin: str):
        tbl = self._calculate(
            data, self.time_bins[time_bin], self.threshold, self.top_n
        )
        return tbl

    def record_metrics(self):
        # Create dataframe with grain of hour of day, start location, end location
        gdf = gpd.read_postgis(star, con=engine, geom_col="linear_distance")

        # Define travel distance
        gdf["miles"] = gdf["linear_distance"].to_crs(UTM10.crs).length * METERS_TO_MILE

        gdf["hour"] = np.floor(gdf["departure"].dt.total_seconds() / 60 / 60).astype(
            int
        )

        for time_bin in self.time_bins:
            description = f"Summary of origin-destinations at the nearest postal city level during the hours of {time_bin}"

            metric(domain=domain, name=f"{time_bin}", description=description,)(
                self.calculate
            )(gdf, time_bin)
