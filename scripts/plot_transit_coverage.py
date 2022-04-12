"""
Creates a hexplot showing distance to nearest transit stop to approximate transit deserts.
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import sqlalchemy as sa

from hcme.config import input_data, mapbox_token
from hcme.crs import UTM10
from hcme.db import engine, models

px.set_mapbox_access_token(mapbox_token)

stops_fp = input_data.gtfs_dir / "stops.txt"

stops_df = pd.read_csv(stops_fp)

stops_gdf = gpd.GeoDataFrame(
    stops_df, geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat)
).set_crs(epsg=4326)

households = gpd.read_postgis(
    sa.select(models.Household, models.Location).join(
        models.Location, models.Household.location_id == models.Location.id
    ),
    con=engine,
    geom_col="coordinates",
)

# join nearest stop
nearest_stop = (
    households.to_crs(UTM10.crs)
    .sjoin_nearest(
        stops_gdf.to_crs(UTM10.crs),
        how="left",
        distance_col="distance_m",
    )
    .to_crs(epsg=4326)
)

nearest_stop["lat"] = nearest_stop.coordinates.y
nearest_stop["long"] = nearest_stop.coordinates.x
nearest_stop["distance_miles"] = nearest_stop["distance_m"] * 0.000621371

fig = ff.create_hexbin_mapbox(
    data_frame=nearest_stop,
    lat="lat",
    lon="long",
    nx_hexagon=100,
    opacity=0.5,
    labels={"color": "Distance"},
    min_count=1,
    color="distance_miles",
    agg_func=np.mean,
    color_continuous_scale=px.colors.diverging.Portland,
    range_color=[0, 1],
)

fig.show()
