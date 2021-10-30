"""
Load county parcel data to locations.
"""
import pandas as pd
import geopandas as gpd
import altair as alt

from pathlib import Path

from hcme.config import input_registry

apn_fp = input_registry.apns
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


taz_fp = Path(data_dir) / "aggregated-taz.kml"

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

if __name__ == "__main__":

    apns = pd.read_csv(apn_fp, usecols=cols)

    # Set coordinates
    apns = gpd.GeoDataFrame(
        apns, geometry=gpd.points_from_xy(apns["long"], apns["lat"])
    )

    # Set a CRS
    apns = apns.set_crs(4326)

    # Fix periods in columns
    apns = apns.rename(columns={"agg.taz": "agg_taz"})
