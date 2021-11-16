"""
Load county parcel data to locations.
"""
import pandas as pd
import geopandas as gpd
import altair as alt
import sqlalchemy as sa

from geoalchemy2 import WKTElement
from sqlalchemy.dialects import postgresql
from shapely.geometry import Point
from pathlib import Path

from hcme.db import Session, engine
from hcme.db.models import Location, TAZ
from hcme.db.io import make_loader, AbstractDataBlock, nan_to_null, Transform

from hcme.config import input_data
from hcme.utils import assert_depends_on, get_nullable_columns


apn_fp = input_data.apns_geocoded

cols = [
    "APN",
    "AREA",
    "PERIMETER",
    "EXLU4",
    "PARCEL",
    "ACRES",
    "SOURCE",
    "ZONING",
    "long",
    "lat",
    "agg.taz",
    "use",
    "type",
    "weight",
]


class APNBlock(AbstractDataBlock):

    reader_kwrags = {"usecols": cols, "dtype": {"": ""}}

    header_map = {
        "agg.taz": "taz_id",
        "APN": "parcel_id",
        "lat": "lat",
        "long": "long",
        "type": "parcel_type",
        "use": "use",
        "ZONING": "zone_type",
        "City": "city",
        "Zip": "zipcode",
        "Full FIPS (block)": "census_block_geoid",
        "Carrier Route Description": "carrier_route_description",
        "Carrier Route ID": "carrier_route_id",
        "Valid delivery area?": "valid_delivery_area",
        "weight": "weight",
    }

    transforms = [
        "drop_data",
        "clean_geoid",
        "clean_postal",
        "create_coordinates",
        "clean_parcel_meta",
        Transform(nan_to_null, defaults={"cols": get_nullable_columns(Location)}),
        "derive_tazs",
    ]

    model = Location

    def create_coordinates(self, df):
        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(x=df["long"], y=df["lat"], crs="EPSG:4326")
        )
        gdf["coordinates"] = gdf.geometry.to_wkt().apply(
            lambda x: WKTElement(x, srid=4326)
        )
        return gdf

    def clean_geoid(self, df):
        df["census_block_geoid"] = df["census_block_geoid"].astype(str).str.zfill(15)
        return df

    def drop_data(self, df):
        """Drop irrelevant rows"""
        # Only keep rows with a taz
        has_taz = df["taz_id"].notnull()
        # Drop all parcels that are not valid locations
        has_parcel_id = df["parcel_id"].fillna("").str.contains(r"^\d+")
        # Has valid use
        # has_use = df["use"].notnull()

        df = df[has_taz & has_parcel_id].copy()

        return df

    def clean_postal(self, df):
        df["zipcode"] = df["zipcode"].astype(str).str[:5]
        df["valid_delivery_area"] = df["valid_delivery_area"] == "Yes"
        return df

    def clean_parcel_meta(self, gdf):
        gdf["residential"] = gdf["parcel_type"] == "residential"
        gdf["use"] = gdf["use"].fillna("Unknown")
        gdf["weight"] = gdf["weight"].fillna(0.0)
        return gdf

    def derive_tazs(self, gdf):
        """
        The original data had some labeling errors which did not properly assign TAZs to the shapefile.
        """
        gdf.drop(columns=["taz_id"], inplace=True)
        # Pull in the TAZ table
        tazs = gpd.read_postgis(
            sa.select(TAZ.id.label("taz_id"), TAZ.geometry),
            geom_col="geometry",
            con=engine,
        )
        gdf = gdf.sjoin(tazs, how="left", predicate="within")
        # Clean borders (some apns lie in two tazs)
        gdf = gdf[~gdf.index.duplicated(keep="first")]
        return gdf


def main():
    """Load APN data to locations."""
    session = Session()
    block = APNBlock(apn_fp)
    gdf = block.parse()
    Loader = make_loader(Location, grain=["parcel_id", "taz_id"])
    # Debug
    # loader = Loader(session, batch_size=1)
    loader = Loader(session, batch_size=10)
    loader.load(gdf.to_dict(orient="records"))


depends_on = (apn_fp,)

if __name__ == "__main__":
    assert_depends_on(depends_on)
    main()
