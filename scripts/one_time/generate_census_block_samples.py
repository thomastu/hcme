"""
Create a single sample point for each block group in the 2020 census from the APN data set.

The purpose of this is to 
"""
import geopandas as gpd
import pandas as pd
from loguru import logger
from tqdm import tqdm

from hcme.config import artifacts, input_data

county_code = "023"

outputs = [artifacts.census_block_address_samples, artifacts.census_block_centroids]


if __name__ == "__main__":

    for output in outputs:
        if output.exists():
            logger.warning(
                "Output file {output} already exists.  Continuing the script will overwrite these files.",
                output=output,
            )

    # Download Block Level Shapefile
    # https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2021&layergroup=Blocks+%282020%29
    census_blocks = gpd.read_file(input_data.census_blocks).to_crs("EPSG:4326")
    # Filter down to Humboldt County only blocks
    humboldt_census_blocks = census_blocks.query("COUNTYFP20 == @county_code")

    apns = pd.read_csv(input_data.apns, usecols=["lat", "long", "APN"])
    apns = gpd.GeoDataFrame(
        apns, geometry=gpd.points_from_xy(apns["long"], apns["lat"], crs="EPSG:4326")
    )

    # For each Census block, pick a random point/address

    samples = []
    centroids = []
    rep_points = []

    for index, row in tqdm(humboldt_census_blocks.iterrows()):
        block_id = row["GEOID20"]
        # Pick a random point from the block
        representative_point = row.geometry.representative_point()
        centroid = row.geometry.centroid

        # Find the closest APN to the representative point
        closest_apn = apns.iloc[apns.distance(representative_point).idxmin()]

        centroids.append(
            {
                "x": centroid.x,
                "y": centroid.y,
                "block_id": block_id,
            }
        )

        rep_points.append(
            {
                "x": representative_point.x,
                "y": representative_point.y,
                "block_id": block_id,
            }
        )

        samples.append(
            {
                "x": closest_apn.geometry.x,
                "y": closest_apn.geometry.y,
                "block_id": block_id,
            }
        )

    pd.DataFrame(samples).to_csv(artifacts.census_block_address_samples, index=False)
    pd.DataFrame(centroids).to_csv(artifacts.census_block_centroids, index=False)
    pd.DataFrame(rep_points).to_csv(artifacts.census_block_rep_points, index=False)
