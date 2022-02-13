"""
Load county parcel data to locations.
"""
import re
from pathlib import Path

import altair as alt
import geopandas as gpd
import pandas as pd
from geoalchemy2 import WKTElement
from loguru import logger
from shapely.geometry import Point
from sqlalchemy.dialects import postgresql
from tqdm import tqdm

from hcme.config import input_data
from hcme.db import Session
from hcme.db.io import AbstractDataBlock, make_loader
from hcme.db.models.registry import (
    CensusBlock,
    CensusBlockAge,
    CensusBlockEconomics,
    CensusBlockHousehold,
)
from hcme.utils import assert_depends_on

data = input_data.census_blocks_geocoded


RE_AGE_COLUMNS = r"ACS Demographics/Population by age range/(?P<sex>.+): (?P<range>.+) years\w*/Percentage"

RE_ECONOMICS_COLUMNS = r"ACS Economics/Household income/(?P<income>.+)/Percentage"

sex_mapping = {"Male": "M", "Female": "F"}

if __name__ == "__main__":
    data = pd.read_csv(input_data.census_blocks_geocoded)
    session = Session()
    census_block_loader = make_loader(CensusBlock, grain=["id"])(session, batch_size=15)
    census_block_age_loader = make_loader(
        CensusBlockAge, grain=["block_id", "sex", "lower_bound"]
    )(session, batch_size=10000)
    census_block_economics_loader = make_loader(
        CensusBlockEconomics,
        grain=[
            "block_id",
            "household_income_lower_bound",
            "household_income_upper_bound",
        ],
    )(session, batch_size=10000)
    census_block_household_loader = make_loader(
        CensusBlockHousehold,
        grain=[
            "block_id",
        ],
    )(session, batch_size=15)

    for idx, r in tqdm(data.iterrows()):
        logger.debug("Processing row {idx} of {total}", idx=idx, total=data.shape[0])
        r = r.fillna(0)
        block_id = f"{r['Full FIPS (block)']:015d}"
        block_id[:2]
        census_block = {
            "id": block_id,
            "state_code": block_id[:2],
            "county_code": block_id[:5],
            "tract_code": block_id[5:11],
            "block_code": block_id[11:],
            "total_population": int(r["ACS Demographics/Sex/Total/Value"]),
            "total_households": int(
                r["ACS Families/Household type by household/Total/Value"]
            ),
            "pct_m": float(r["ACS Demographics/Sex/Male/Percentage"]),
            "pct_f": float(r["ACS Demographics/Sex/Female/Percentage"]),
            "pct_family_household": float(
                r[
                    "ACS Families/Household type by household/Family households/Percentage"
                ]
            ),
        }
        census_block_loader.stream(census_block)

        for col in r.index[r.index.str.match(RE_AGE_COLUMNS)]:
            m = re.match(RE_AGE_COLUMNS, col).groupdict()
            sex = m["sex"]

            age_range = re.findall("\d+", m["range"])
            if len(age_range) == 1:
                bound = int(age_range[0])
                if ": Under" in col:
                    upper_bound = bound
                    lower_bound = 0
                elif "and over" in col:
                    upper_bound = 100
                    lower_bound = bound
                else:
                    upper_bound = bound
                    lower_bound = bound
            elif len(age_range) == 2:
                lower_bound, upper_bound = map(int, age_range)
            else:
                raise ValueError(f"Invalid age column: {col}")

            census_block_age = {
                "block_id": block_id,
                "pct": r[col],
                "count": r[col.replace("Percentage", "Value")],
                # FIXME: TBD whether this is important
                "pct_veteran": 0,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "sex": sex_mapping[sex],
            }
            census_block_age_loader.stream(census_block_age)

        census_block_household = {
            "block_id": block_id,
            "pct_family_household": r[
                "ACS Families/Household type by household/Family households/Percentage"
            ],
            "pct_nonfamily_household": 1
            - r[
                "ACS Families/Household type by household/Family households/Percentage"
            ],
            "pct_nonfamily_alone": r[
                "ACS Families/Household type by household/Nonfamily households: Householder living alone/Percentage"
            ],
        }
        # print(census_block_household)
        census_block_household_loader.stream(census_block_household)

        for col in r.index[r.index.str.match(RE_ECONOMICS_COLUMNS)]:
            income_bracket = re.findall("[\d,]+", col)
            if len(income_bracket) == 1:
                bound = float(income_bracket[0].replace(",", ""))
                if "Less than" in col:
                    household_income_lower_bound = 0
                    household_income_upper_bound = bound
                elif "or more" in col:
                    household_income_lower_bound = bound
                    household_income_upper_bound = bound + 50000
                else:
                    raise ValueError(f"Invalid econ column: {col}")
            elif len(income_bracket) == 2:
                lower, upper = map(lambda x: int(x.replace(",", "")), income_bracket)
                household_income_lower_bound = lower
                household_income_upper_bound = upper
            census_block_economics = {
                "block_id": block_id,
                "pct": r[col],
                "household_income_lower_bound": household_income_lower_bound,
                "household_income_upper_bound": household_income_upper_bound,
            }
            census_block_economics_loader.stream(census_block_economics)

    census_block_loader.flush()
    census_block_age_loader.flush()
    census_block_economics_loader.flush()
    census_block_household_loader.flush()
