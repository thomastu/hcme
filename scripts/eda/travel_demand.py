"""This script is responsible for generating the following outputs:

1. Job Flow Travel Demand by City or Region
"""
import altair as alt
import geopandas as gpd
import numpy as np
import pandas as pd
import sqlalchemy as sa

from hcme.config import input_data
from hcme.db import Session
from hcme.db.models import TAZ

session = Session()

demand = pd.read_csv(input_data.demand, sep="\t")
tazs = gpd.read_postgis(
    sa.select(TAZ), session.bind.engine, geom_col="geometry", index_col="id"
)
utm_crs = tazs.estimate_utm_crs()

tazs["centroid"] = tazs.to_crs(utm_crs).geometry.centroid

demand["from_taz"] = demand["from"].map(tazs["name"])
demand["from_centroid"] = demand["from"].map(tazs["centroid"])

demand["to_taz"] = demand["to"].map(tazs["name"])
demand["to_centroid"] = demand["to"].map(tazs["centroid"])

demand["departure_hour"] = np.floor(demand["depart"])

demand["naive_distance"] = gpd.GeoSeries(demand["from_centroid"]).distance(
    gpd.GeoSeries(demand["to_centroid"])
)

demand.index = demand.index.rename("trip_id")

demand = demand.reset_index()
