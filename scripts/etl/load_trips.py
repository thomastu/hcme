"""Generate a travel diary for an input population.

# Algorithm for Demand Characteristics

1. For each home TAZ, select floor(num_travelers, num_households) - if we have more travelers than households, then we will try to build multi-traveler households.  If we have more households than travelers, we will have to discard certain households.

2. Then for each household, build household characteristics.


Facets for microtransit:

- Age > (some cutoff)
- Renter vs Owner
- Income band
- Veteran Status
- Home value
"""
from collections import defaultdict
from datetime import timedelta

import numpy as np
import pandas as pd
import sqlalchemy as sa
from tqdm import tqdm

from hcme.config import input_data
from hcme.db import Session, engine, models
from hcme.db.io import AbstractDataBlock, make_loader
from hcme.metrics import Recorder

input_data.drivers
"""
;driver      int64
from         int64
to           int64
depart     float64
home         int64
"""

TripLoader = make_loader(models.Trip, grain=["person_id", "trip_leg"])

if __name__ == "__main__":

    session = Session()
    recorder = Recorder(
        name="travel-diary-summaries",
        domain="demand",
        description="Travel Diary Summaries",
        provenance=__file__,
    )

    loader = TripLoader(session, batch_size=10000)

    # Rename columns
    drivers = pd.read_table(input_data.drivers, sep="\t")
    drivers = drivers.rename(columns={";driver": "person_id"})

    sorted_trips = drivers.sort_values(["person_id", "depart"])

    # Mark which trips are the first trip for each person
    first_trips = sorted_trips.drop_duplicates(subset=["person_id"], keep="first")
    sorted_trips["first_trip"] = False
    sorted_trips.loc[first_trips.index, "first_trip"] = True

    # Mark the last trip for each person
    last_trips = sorted_trips.drop_duplicates(subset=["person_id"], keep="last")
    sorted_trips["last_trip"] = False
    sorted_trips.loc[last_trips.index, "last_trip"] = True

    # Calculate the leg ID for each person's trip
    num_trips_per_person = sorted_trips.groupby("person_id").size()
    sorted_trips["trip_leg"] = (
        sorted_trips["first_trip"] * ~sorted_trips["last_trip"]
        + sorted_trips["person_id"].map(num_trips_per_person)
        * sorted_trips["last_trip"]
    )
    sorted_trips["trip_leg"] = (
        sorted_trips["trip_leg"].replace(0, value=np.nan).interpolate().astype(int)
    )

    home_locations = pd.read_sql_query(
        sa.select(
            models.Person.id.label("person_id"),
            models.Location.id.label("home_location_id"),
        )
        .join(
            models.Household,
            models.Person.household_id == models.Household.id,
        )
        .join(
            models.Location,
            models.Household.location_id == models.Location.id,
        ),
        con=engine,
        index_col="person_id",
    )["home_location_id"]

    destinations = pd.read_sql_query(
        sa.select(models.Location).where(
            models.Location.residential == False,
        ),
        engine,
    )

    for person_id, group in tqdm(sorted_trips.groupby(["person_id"], as_index=False)):
        home_location_id = home_locations.loc[person_id]
        # Sort by trip leg
        origin_location_id = None
        for idx, row in group.sort_values(["trip_leg"]).iterrows():
            from_taz_id = row["from"]
            to_taz_id = row["to"]
            if not origin_location_id:
                origin_location_id = (
                    destinations.query("taz_id == @from_taz_id")
                    .sample(1, weights="weight")
                    .iloc[0]["id"]
                )
            destination_location_id = (
                destinations.query("taz_id == @to_taz_id")
                .sample(1, weights="weight")
                .iloc[0]["id"]
            )
            if to_taz_id == row["home"] and row["last_trip"] == True:
                destination_location_id = home_location_id
            elif from_taz_id == row["home"] and row["first_trip"] == True:
                origin_location_id = home_location_id

            loader.stream(
                {
                    "person_id": int(person_id),
                    "trip_leg": int(row["trip_leg"]),
                    "departure": timedelta(hours=row["depart"]),
                    "origin_location_id": int(origin_location_id),
                    "destination_location_id": int(destination_location_id),
                }
            )
            # Set the next origin as the current destination
            origin_location_id = destination_location_id

    loader.flush()
