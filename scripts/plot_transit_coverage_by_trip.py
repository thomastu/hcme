import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import polars as pl
import sqlalchemy as sa

from hcme.config import artifacts, input_data, mapbox_token
from hcme.crs import UTM10
from hcme.db import engine, models

px.set_mapbox_access_token(mapbox_token)

time_bins = {
    "morning": [*range(5, 11)],
    "noon": [*range(11, 17)],
    "evening": [*range(17, 23)],
    "night": [*range(0, 5), *range(23, 25)],
}

if __name__ == "__main__":
    stops = input_data.gtfs_dir / "stops.txt"
    schedules = input_data.gtfs_dir / "stop_times.txt"

    stops_df = pl.read_csv(stops)
    schedules_df = pl.read_csv(schedules)
    df = schedules_df.join(stops_df, on="stop_id", how="left").to_pandas()
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.stop_lon, df.stop_lat),
    ).set_crs(epsg=4326)
    trips = gpd.read_postgis(
        sa.select(models.Trip, models.Location.coordinates).join(
            models.Location, models.Trip.origin_location_id == models.Location.id
        ),
        con=engine,
        geom_col="coordinates",
    )

    # join nearest stop
    nearest_stop = (
        trips.to_crs(UTM10.crs)
        .sjoin_nearest(
            gdf.to_crs(UTM10.crs),
            how="left",
            distance_col="distance_m",
        )
        .to_crs(epsg=4326)
    )
    nearest_stop["distance_miles"] = nearest_stop["distance_m"] * 0.000621371
    nearest_stop["wait"] = (
        pd.to_timedelta(nearest_stop["arrival_time"]) - nearest_stop["departure"]
    ) % pd.to_timedelta("1 day 0:00:00")
    nearest_stop["wait_minutes"] = nearest_stop["wait"].dt.total_seconds() / 60
    nearest_stop = nearest_stop.sort_values(["person_id", "id", "wait"]).drop_duplicates(
        subset="id", keep="first"
    )
    nearest_stop["latitude"] = nearest_stop.geometry.y
    nearest_stop["longitude"] = nearest_stop.geometry.x
    nearest_stop["hour"] = np.floor(nearest_stop["departure"].dt.total_seconds() / 60 / 60).astype(
        int
    )

    for time_bin, hours in time_bins.items():
        data = nearest_stop[nearest_stop["hour"].isin(hours)]
        plt = ff.create_hexbin_mapbox(
            data,
            lat="latitude",
            lon="longitude",
            nx_hexagon=100,
            opacity=0.5,
            labels={"color": "Distance"},
            min_count=1,
            color="distance_miles",
            agg_func=np.mean,
            zoom=7,
            color_continuous_scale=px.colors.diverging.Portland,
            range_color=[0, 0.5],
        )

        plt.update_geos(fitbounds="locations", projection={"scale": 1})
        plt.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

        fp = artifacts.figures / f"transit_coverage/trip_dist_{time_bin}.png"
        fp.parent.mkdir(parents=True, exist_ok=True)
        plt.write_image(str(fp), scale=2)
        plt.write_html(str(fp) + ".html")

        plt = ff.create_hexbin_mapbox(
            data,
            lat="latitude",
            lon="longitude",
            nx_hexagon=100,
            opacity=0.5,
            labels={"color": "Wait Time"},
            min_count=1,
            zoom=7,
            color="wait_minutes",
            agg_func=np.mean,
            range_color=[0, 60],
            color_continuous_scale=px.colors.diverging.Portland,
        )

        plt.update_geos(fitbounds="locations", projection={"scale": 1})
        plt.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fp = artifacts.figures / f"transit_coverage/wait_time_{time_bin}.png"
        fp.parent.mkdir(parents=True, exist_ok=True)
        plt.write_image(str(fp), scale=2)
        plt.write_html(str(fp) + ".html")
