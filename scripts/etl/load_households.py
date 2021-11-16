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

import pandas as pd
import sqlalchemy as sa

from hcme.config import input_data
from hcme.db import Session, engine, models
from hcme.db.io import make_loader
from hcme.metrics import Recorder
from tqdm import tqdm

if __name__ == "__main__":

    session = Session()
    recorder = Recorder(
        name="household-generation",
        domain="location",
        description="TAZ-level population statistics",
        provenance=__file__,
    )

    drivers = pd.read_table(input_data.drivers, sep="\t")
    drivers = drivers.rename(columns={";driver": "person_id"})

    person_loader = make_loader(models.Person, grain=["id"])(session, batch_size=1000)

    summary_statistics = []
    for taz_id, taz_df in tqdm(drivers.groupby("home")):
        # Only take unique people
        persons = taz_df.drop_duplicates(subset=["person_id"], keep="first")
        # Pull possible residences for this TAZ
        residential_locations = pd.read_sql_query(
            sa.select(
                models.Location.id,
                models.Location.weight,
                sa.func.count(models.Household.id).label("n_households"),
            )
            .join(models.Household, isouter=True)
            .where(
                models.Location.taz_id == taz_id,
                sa.or_(
                    models.Location.residential == True,
                    # Allow for motels to be included
                    models.Location.use.ilike("%motel%"),
                ),
                sa.not_(models.Location.use.ilike("%vacant%")),
            )
            .group_by(models.Location.id),
            con=engine,
            index_col="id",
        )

        # Calculate weights to attempt to balance number of people per household toward 1-2 people per household

        households_cache = pd.read_sql_query(
            sa.select(
                models.Household.id.label("household_id"),
                models.Household.location_id,
                sa.func.count(models.Household.members).label("n_members"),
            )
            .join(
                models.Location,
                models.Household.location_id == models.Location.id,
                isouter=True,
            )
            .join(
                models.Person,
                models.Household.id == models.Person.household_id,
                isouter=True,
            )
            .where(
                models.Location.taz_id == taz_id,
            )
            .group_by(models.Household.id),
            con=engine,
        )
        # household to location mapping
        # For each traveler...
        for n, person in tqdm(enumerate(persons.to_dict(orient="records"))):

            # Recalculate weights to account for previous assignments
            # Statistically, roughly half of households should end up as 2-person households
            # weights = (
            #     residential_locations["weight"]
            #     + residential_locations["n_households"] / 2
            # )

            # Sample a location
            location_id = (
                residential_locations.sample(weights="weight", n=1).iloc[0].name
            )
            location_row = residential_locations.loc[location_id]
            if location_row["n_households"] == location_row["weight"]:
                # We have selected all available households!
                # Now reassign person to existing household
                household_row = (
                    households_cache[households_cache["location_id"] == location_id]
                    .sample(weights="n_members")
                    .iloc[0]
                )
                idx = household_row.name
                household_id = household_row["household_id"]
                households_cache.loc[idx, "n_members"] += 1
            # Update weights
            else:
                residential_locations.loc[location_id, "n_households"] += 1
                household = models.Household(location_id=int(location_id))
                session.add(household)
                session.commit()
                household_id = household.id
                households_cache = households_cache.append(
                    {
                        "household_id": household_id,
                        "location_id": location_id,
                        "n_members": 1,
                    },
                    ignore_index=True,
                )

            # Look at remaining households:

            # Stream to personLoader
            person_loader.stream(
                {"id": person["person_id"], "household_id": household_id}
            )

        summary_statistics.append(
            {
                "taz_id": taz_id,
                "num_travlers": taz_df["person_id"].nunique(),
                "people_per_residences": taz_df["person_id"].nunique()
                / residential_locations.shape[0],
            }
        )
    person_loader.flush()
    recorder.record(summary_statistics)
