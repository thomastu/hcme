import geopandas as gpd
import numpy as np
import plotly.express as px
import sqlalchemy as sa
from plotly.subplots import make_subplots

from hcme.config import artifacts, mapbox_token
from hcme.db import engine, models
from hcme.demand.summary import DemandMatrix

px.set_mapbox_access_token(mapbox_token)

Trip = models.Trip
Person = models.Person
Household = models.Household

Location = models.Location
Destination = sa.orm.aliased(Location)
Home = sa.orm.aliased(Location)
Origin = sa.orm.aliased(Location)

time_bins = {
    "morning": [*range(5, 11)],
    "noon": [*range(11, 17)],
    "evening": [*range(17, 23)],
    "night": [*range(0, 5), *range(23, 25)],
}

if __name__ == "__main__":
    q = (
        sa.select(
            Trip,
            Destination.coordinates.label("destination_coordinates"),
            Origin.coordinates.label("origin_coordinates"),
            Destination.city.label("destination_city"),
            Origin.city.label("origin_city"),
        )
        .join(Destination, Trip.destination_location_id == Destination.id)
        .join(Origin, Trip.origin_location_id == Origin.id)
        .join(Person, Trip.person_id == Person.id)
        .join(Household, Person.household_id == Household.id)
        .join(Home, Household.location_id == Home.id)
    )

    origins = gpd.read_postgis(q, con=engine, geom_col="origin_coordinates")
    destinations = gpd.read_postgis(q, con=engine, geom_col="destination_coordinates")

    for gdf in [origins, destinations]:
        gdf["hour"] = np.floor(gdf["departure"].dt.total_seconds() / 60 / 60).astype(int)
        gdf["latitude"] = gdf.geometry.y
        gdf["longitude"] = gdf.geometry.x

    for category, gdf in [("origin", origins), ("destination", destinations)]:
        row, col = 1, 1
        for i, (time_bin, hours) in enumerate(time_bins.items(), start=1):
            row += i % 2
            col = (i % 2) or 2
            data = gdf[gdf["hour"].isin(hours)]
            center = data.dissolve().centroid
            center = dict(lat=float(center.y), lon=float(center.x))
            plt = px.density_mapbox(
                data,
                lat="latitude",
                lon="longitude",
                radius=2,
                center=center,
                zoom=10,
                width=1000,
                height=1000,
            )
            plt.update_coloraxes(showscale=False)
            plt.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            fp = artifacts.figures / f"trip_density/{category}/county/{time_bin}.png"
            fp.parent.mkdir(parents=True, exist_ok=True)
            plt.write_image(str(fp), scale=2)

    places = [
        "Arcata",
        "Eureka",
        "Fortuna",
        "Mckinleyville",
        "Willow Creek",
        "Blue Lake",
        "Bayview",
        "Trinidad",
        "Orick",
        "Cutten",
    ]
    for city in places:
        # Where are you going to coming from {city}?
        # Filter by origin and then map density of destinations

        gdf = destinations[destinations["origin_city"] == city]
        for time_bin, hours in time_bins.items():
            data = gdf[gdf["hour"].isin(hours)]
            center = data.dissolve().representative_point()
            center = dict(lat=float(center.y), lon=float(center.x))
            plt = px.density_mapbox(
                data,
                lat="latitude",
                lon="longitude",
                radius=1,
                # center=center,
                zoom=9,
                # title=time_bin,
                width=1000,
                height=1000,
            )
            plt.update_geos(fitbounds="locations", projection={"scale": 1})
            plt.update_coloraxes(showscale=False)
            plt.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            fp = artifacts.figures / f"trip_density/origin/{city}/{time_bin}.png"
            fp.parent.mkdir(parents=True, exist_ok=True)
            plt.write_image(str(fp), scale=2)

    for city in places:
        # Where are you coming from to get to {city}?
        # Filter by origin and then map density of destinations
        gdf = origins[origins["destination_city"] == city]
        for time_bin, hours in time_bins.items():
            data = gdf[gdf["hour"].isin(hours)]
            center = data.dissolve().representative_point()
            center = dict(lat=float(center.y), lon=float(center.x))
            plt = px.density_mapbox(
                data,
                lat="latitude",
                lon="longitude",
                radius=1,
                # center=center,
                zoom=9,
                # title=time_bin,
                width=1000,
                height=1000,
            )
            plt.update_geos(fitbounds="locations", projection={"scale": 1})
            plt.update_coloraxes(showscale=False)
            plt.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            fp = artifacts.figures / f"trip_density/destination/{city}/{time_bin}.png"
            fp.parent.mkdir(parents=True, exist_ok=True)
            plt.write_image(str(fp), scale=2)
