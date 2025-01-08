from functools import reduce

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import sqlalchemy as sa
from geoalchemy2.functions import ST_LineMerge
from shapely import geometry

from hcme import config
from hcme.beam.events.registry import Registry
from hcme.db import Session, engine, models

mapbox_token = config.mapbox_token

px.set_mapbox_access_token(mapbox_token)


def read_events(beam_output_dir):
    r = Registry(beam_output_dir)
    # Columns to keep for person events
    event_cols = [
        "person",
        "vehicle",
        "time",
        "link",
        "type",
        "legMode",
        "location",
        "mode",
        "currentTourMode",
        "personalVehicleAvailable",
        "tourIndex",
        "availableAlternatives",
    ]
    events = pd.read_csv(r.events, usecols=event_cols, dtype={"person": str, "vehicle": str})

    vehicle_cols = ["person", "vehicle", "time", "link", "type"]

    # Re-order events to ensure contiguous sequence
    physsim = pd.read_csv(
        r.physsim,
        usecols=vehicle_cols,
    )

    return events, physsim


def create_person_route(person_id):
    pass


if __name__ == "__main__":

    beam_output_dir = "/home/ttu/Storage1/hcme-beam-runs/hcme__2022-01-03_15-03-54_ehb"
    agents, vehicles = read_events(beam_output_dir)

    # Query for single person
    person_id = "10064"

    # This will exclude `PathTraversal`, `LeavingParkingEvent`, and `ParkingEvent` types
    agent = agents.query("person == @person_id")

    # Get trip leg time boxes
    enters_vehicle = agent["type"] == "PersonEntersVehicle"
    exits_vehicle = agent["type"] == "PersonLeavesVehicle"

    # Add a 1-second buffer
    windows = zip(
        zip(agent[enters_vehicle]["time"], agent[exits_vehicle]["time"]),
        agent[enters_vehicle]["vehicle"],
    )

    mask = reduce(
        lambda a, b: a | b,
        (
            vehicles["time"].between(*window[0], inclusive="both")
            & (vehicles["vehicle"] == window[1])
            for window in windows
        ),
        vehicles["time"].isnull(),
    )

    events = agent.append(vehicles[mask]).sort_values(by=["time"])

    # We have a route! now need to link this back to the OSM network...
    route = events["link"].dropna().drop_duplicates(keep="first").astype(int).to_list()

    # Now that we have a route, let's make a linestring
    session = Session()

    session.query()
    linestring = []

    ordering = {k: v for v, k in enumerate(route)}

    q = sa.select(models.Link.id, models.Link.geometry.label("geometry")).where(
        models.Link.id.in_(route)
    )

    gdf = gpd.read_postgis(q, con=engine, geom_col="geometry")

    gdf["route_order"] = gdf["id"].map(ordering)

    gdf.sort_values(by="route_order", inplace=True)

    linestrings = gdf["geometry"].to_list()

    lats = []
    lons = []
    names = []

    for i, linestring in enumerate(linestrings):
        x, y = linestring.xy
        lats = np.append(lats, y)
        lons = np.append(lons, x)
        names = np.append(names, [f"Leg: {i}"] * len(y))
        lats = np.append(lats, None)
        lons = np.append(lons, None)
        names = np.append(names, None)
    fig = px.line_mapbox(lat=lats, lon=lons, hover_name=names, color="red")
    fig.update_geos(fitbounds="locations")

    fig.show()
