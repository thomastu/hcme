import geopandas as gpd
import numpy as np
import sqlalchemy as sa

import plotly.express as px
import plotly.figure_factory as ff
from sqlalchemy.sql.functions import count

from hcme.config import mapbox_token
from hcme.db import Trip, engine, models

px.set_mapbox_access_token(mapbox_token)
Destination = sa.orm.aliased(models.Location)
Origin = sa.orm.aliased(models.Location)

if __name__ == "__main__":

    df = px.data.carshare()
    # Get trip data
    gdf = gpd.read_postgis(
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
    # Define lat/long columns
    gdf["lat"] = gdf.geometry.y
    gdf["long"] = gdf.geometry.x
    gdf["hour"] = ((gdf["departure"].dt.total_seconds() / 60 / 60) // 1).astype(int)

    fig = ff.create_hexbin_mapbox(
        data_frame=gdf,
        lat="lat",
        lon="long",
        nx_hexagon=125,
        opacity=0.5,
        labels={"color": "Count"},
        min_count=1,
        animation_frame="hour",
        # color="id",
        # agg_func=lambda x: np.log(np.size(x)),
        color_continuous_scale=px.colors.diverging.RdBu_r,
        color_continuous_midpoint=50,
        range_color=[0, 100],
    )

    fig.show()
