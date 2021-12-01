"""WIP: create origin-destination point size plots.
"""

from datetime import datetime

import folium
import geoalchemy2 as ga
import geopandas as gpd
import geoviews as gv
import geoviews.feature as gf
import geoviews.tile_sources as gvts
import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
import param
import sqlalchemy as sa
from hcme.db import engine, models
from hcme.demand import summary as demand_summary
from pyproj import Proj

gv.extension("bokeh")

gv.output(fig="html")
hv.opts.defaults(
    hv.opts.Tiles(tools=["save"], width=400, xaxis=None, yaxis=None, border=0, margin=0)
)

Trip = models.Trip
Person = models.Person
Household = models.Household
Metrics = models.Metrics

Location = models.Location
Destination = sa.orm.aliased(Location)
Home = sa.orm.aliased(Location)
Origin = sa.orm.aliased(Location)

UTM10 = Proj(proj="utm", zone=10, ellps="WGS84")

if __name__ == "__main__":
    persons = gpd.read_postgis(
        sa.select(
            Person,
            Location.coordinates,
            Location.city,
            Location.id.label("location_id"),
            models.TAZ.id.label("taz_id"),
            models.TAZ.name.label("taz_name"),
        )
        .join(Household, Person.household_id == Household.id)
        .join(Location, Household.location_id == Location.id)
        .join(models.TAZ, Location.taz_id == models.TAZ.id),
        con=engine,
        geom_col="coordinates",
    )

    # Aggregate people over neighborhoods by "Dissolving"
    centroids = persons.dissolve(by="city", aggfunc="count").representative_point()

    # Get trips by Origin city
    trips = gpd.read_postgis(
        sa.select(
            Trip,
            Origin.city.label("origin_city"),
            Origin.coordinates,
            Destination.city.label("destination_city"),
        )
        .join(Origin, Trip.origin_location_id == Origin.id)
        .join(Destination, Trip.destination_location_id == Destination.id),
        con=engine,
        geom_col="coordinates",
    )

    trips["hour"] = ((trips["departure"].dt.total_seconds() / 60 / 60) // 1).astype(int)
    destination_trip_counts = trips.groupby(
        ["hour", "destination_city"], as_index=False
    ).agg(num_trips=("id", "count"))
    origin_trip_counts = trips.groupby(["hour", "origin_city"], as_index=False).agg(
        num_trips=("id", "count")
    )

    location_points = gpd.GeoDataFrame(
        centroids.rename("geometry").reset_index()
    ).set_geometry("geometry")

    tazs = gpd.read_postgis(sa.select(models.TAZ), con=engine, geom_col="geometry")

    basemap = gv.tile_sources.OSM.opts()

    class Hour(param.Parameterized):
        hour = param.Integer(default=12, bounds=(0, 24))

        def chloro(self, loc):

            data = location_points.copy()
            if loc == "origin":
                trip_counts = origin_trip_counts
                idx = "origin_city"
                mapper = trip_counts[trip_counts["hour"] == self.hour].set_index(idx)[
                    "num_trips"
                ]
            elif loc == "destination":
                trip_counts = destination_trip_counts
                idx = "destination_city"
                mapper = trip_counts[trip_counts["hour"] == self.hour].set_index(idx)[
                    "num_trips"
                ]
            else:
                mapper = origin_trip_counts[
                    origin_trip_counts["hour"] == self.hour
                ].set_index("origin_city")["num_trips"].fillna(
                    0
                ) - destination_trip_counts[
                    destination_trip_counts["hour"] == self.hour
                ].set_index(
                    "destination_city"
                )[
                    "num_trips"
                ].fillna(
                    0
                )

            data["num_trips"] = data["city"].map(mapper).fillna(0)
            plt = gv.Points(data, vdims=["num_trips", "city"]).opts(
                size=np.log2(abs(gv.dim("num_trips")) + 1) * 1.75,
                fill_color="num_trips",
                cmap="viridis",
                tools=["hover", "save"],
                line_color="white",
            )

            return plt

        @param.depends("hour")
        def origin(self):
            plt = self.chloro("origin")
            return (basemap * plt).opts(**opts)

        @param.depends("hour")
        def destination(self):
            plt = self.chloro("destination")
            return (basemap * plt).opts(**opts)

        @param.depends("hour")
        def net(self):
            plt = self.chloro("net")
            return (basemap * plt).opts(**opts)

    p = Hour()

    pn.Row(p.param, p.origin, p.destination)
    pn.Row(p.param, p.net)
