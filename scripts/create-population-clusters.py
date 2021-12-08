import sqlalchemy as sa
import geopandas as gpd
import numpy as np

import geoviews as gv
import holoviews as hv
from hcme.crs import UTM10
from hcme.db import models, engine
from hcme.config import artifacts
from sklearn.cluster import DBSCAN, OPTICS

# Approach for seeding microtransit fleet: For each city-location, create a fleet at weighted population centroid
# (i.e. weighted by population density)
# For each analysis zone, record cluster size, cluster centroid,

# Group each TAZ into city clusters
# Use each city zone/cluster to determine where population density exists by attributes such as vehicle ownership


gv.extension("bokeh")

if __name__ == "__main__":

    population = gpd.read_postgis(
        sa.select(
            models.Person,
            models.Location.city,
            models.Location.coordinates,
            models.Location.taz_id,
        )
        .join(
            models.Household,
            models.Person.household_id == models.Household.id,
        )
        .join(models.Location, models.Household.location_id == models.Location.id),
        con=engine,
        geom_col="coordinates",
    )

    tazs = gpd.read_postgis(sa.select(models.TAZ), con=engine, geom_col="geometry")

    taz_most_common_city = (
        population.sjoin(tazs, predicate="within")[["taz_id", "city", "name"]]
        .groupby("taz_id")["city"]
        .value_counts()
        .rename("count")
        .reset_index()
        .drop_duplicates(subset="taz_id", keep="first")
    )

    utm10_coords = population["coordinates"].to_crs(UTM10.crs)

    # DBSCAN requires coordinate system to show up in units of distance
    population["x"] = utm10_coords.geometry.x
    population["y"] = utm10_coords.geometry.y

    city_taz_mapping = {}

    for city, _tazs in taz_most_common_city.groupby("city"):
        city_taz_mapping[city] = _tazs["taz_id"].tolist()

    for city, taz_ids in city_taz_mapping.items():

        # Filter Data
        gdf = population.query("taz_id in @taz_ids").copy()
        gdf["long"] = gdf["coordinates"].geometry.x
        gdf["lat"] = gdf["coordinates"].geometry.y

        # Set Parameters
        eps = 175  # meters
        minpts = max(3, int(0.005 * len(gdf)))  # smallest cluster size allowed

        # Define Clustering Algo
        optics = OPTICS(min_samples=minpts, max_eps=eps, cluster_method="dbscan")

        # Create clusters
        gdf["cluster_id"] = optics.fit_predict(gdf[["y", "x"]])

        # Record cluster statistics
        clusters = gdf["cluster_id"].value_counts()
        clusters.index.rename("cluster_id", inplace=True)
        clusters = clusters.rename("size").reset_index()
        clusters["representative_point"] = clusters["cluster_id"].map(
            gdf.dissolve("cluster_id").geometry.representative_point()
        )
        clusters["city"] = city
        clusters = gpd.GeoDataFrame(clusters, geometry="representative_point")

        # Plot results
        points = gv.Points(
            gdf,
            kdims=["long", "lat"],
            vdims=["cluster_id", "city"],
        ).opts(
            size=8,
            color="cluster_id",
            cmap="glasbey_hv",from hcme.config import artifacts
            active_tools=["wheel_zoom"],
            width=600,
            height=800,
            tools=["hover"],
        )

        basemap = gv.tile_sources.StamenToner.opts()

        hv.save((basemap * points), f"{artifacts}/{city}-clusters.png", fmt="png")
        clusters.to_csv(f"{artifacts}/{city}-clusters.csv", index=False)
