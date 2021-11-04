"""
Load county parcel data to locations.
"""
import pandas as pd
import geopandas as gpd
import altair as alt

from geoalchemy2 import WKTElement
from sqlalchemy.dialects import postgresql
from shapely.geometry import Point
from pathlib import Path

from hcme.db import Session
from hcme.db.models.registry import Location
from hcme.db.io import make_loader, AbstractDataBlock

from hcme.config import input_data
from hcme.utils import assert_depends_on

apn_fp = input_data.apns
"""
APN            object
AREA          float64
PERIMETER     float64
EXLU4          object
BKPG          float64
PARCEL         object
ACRES         float64
SOURCE         object
EDITORNAME     object
LASTUPDATE     object
USECODE       float64
NEIGHCODE     float64
SITHSNBR       object
SITHSNBRSF     object
SITSTDIR       object
SITSTNAME      object
SITSTTYPE      object
SITCITY        object
SITZIP         object
ZONING         object
GEN_PLAN       object
long          float64
lat           float64
taz           float64
agg.taz       float64
zip           float64
tract         float64
use            object
type           object
weight        float64
"""

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

    reader_kwrags = {"usecols": cols}

    header_map = {
        "agg.taz": "taz_id",
        "APN": "parcel_id",
        "lat": "lat",
        "long": "long",
        "type": "parcel_type",
        "use": "use",
        "ZONING": "zone_type",
    }

    transforms = [
        "drop_data",
        "create_coordinates",
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

    def drop_data(self, df):
        """Drop irrelevant rows"""
        # Only keep rows with a taz
        has_taz = df["taz_id"].notnull()
        # Drop all parcels that are not valid locations
        has_parcel_id = df["parcel_id"].fillna("").str.contains(r"^\d+")
        df = df[has_taz & has_parcel_id].copy()
        return df


def main():
    """Load APN data to locations."""
    session = Session()
    block = APNBlock(apn_fp)
    gdf = block.parse()
    Loader = make_loader(Location, grain=["parcel_id", "taz_id"])
    loader = Loader(session, batch_size=10000)
    loader.load(gdf.to_dict(orient="records"))


depends_on = (apn_fp,)

if __name__ == "__main__":
    assert_depends_on(depends_on)
    main()
