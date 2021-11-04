"""

Algorithim for assigning households:

#. For each driver, find the first "from" and the last "to"
#. Filter only for drivers where first and last trip
"""
import pandas as pd
import sqlalchemy as sa

from hcme.config import input_data
from hcme.db import Session
from hcme.db.io import AbstractDataBlock, make_loader
from hcme.db.models.registry import Household, Person, Location

from typing import Dict

# id,from,to,depart
# 1,a,b,10
# 2,c,b,10


def get_or_create_household(home_taz: int) -> Dict:
    """
    Assign a random residential location as a household.
    """
    with Session() as session:
        # Filter for a random location that is not a household yet
        session.execute(
            sa.select(Location)
            .where(
                (Location.taz_id == home_taz)
                & (sa.func.count(Household.id) == 0)
                & (Location.residential == True)
            )
            .order_by(sa.func.random())
            .first()
        )

        household = (
            session.query(Household).filter(Household.home_taz == home_taz).first()
        )
        if not household:
            household = Household(home_taz=home_taz)
            session.add(household)
            session.commit()
        return household


def create_person_mapping(household: Household) -> Dict:
    """Create a person object with characteristics based on household weights."""
    # Figure out existing household characteristics
    # Assign characteristics to new person

    return {
        "household_id": household.id,
    }


session = Session()
PersonLoader = make_loader(Person, grain=["household_id", "id"])
HouseholdLoader = make_loader(Household, grain=[])

if __name__ == "__main__":

    drivers = input_data.drivers
    df = pd.read_table(drivers, sep="\t", index_col=0)

    person_loader = PersonLoader(session, batch_size=10000)
    household_loader = HouseholdLoader(session, batch_size=1)

    for id_, grp in df.groupby(["id"], as_index=False):
        diary = grp.sort_values("depart")
        first_trip = diary.iloc[0, "from"]
        last_destination = diary.iloc[-1, "to"]
        if first_trip == last_destination:
            # Assign home TAZ to household
            home_taz_id = first_trip

            # Filter locations for a residential use address
            # Decide whether to assign to multi-person or single-person household
            # Get or Create household
            household = get_or_create_household(home_taz_id)
            household_loader.stream(household)

            # Create a person
            person = create_person_mapping(household)
            person_loader.stream(person)

    person_loader.flush()
    household_loader.flush()
