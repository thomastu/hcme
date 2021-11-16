"""
Census data used to generate population attributes.
Data are at the census block level and represent percentages.
"""
import sqlalchemy as sa
from hcme.db.abstract import Base


class CensusBlock(Base):

    __tablename__ = "census_block"

    # 15 character GEO ID for census data
    id = sa.Column(
        sa.String(length=15),
        unique=True,
        nullable=False,
        primary_key=True,
        autoincrement=False,
    )

    state_code = sa.Column(sa.String(length=2), nullable=False)

    county_code = sa.Column(sa.String(length=5), nullable=False)

    tract_code = sa.Column(sa.String(length=6), nullable=False)

    block_code = sa.Column(sa.String(length=4), nullable=False)

    # Aggregate Attributes
    total_population = sa.Column(sa.Integer, nullable=False)

    total_households = sa.Column(sa.Integer, nullable=False)

    pct_m = sa.Column(sa.Float, nullable=False)

    pct_f = sa.Column(sa.Float, nullable=False)

    pct_family_household = sa.Column(sa.Float, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("state_code", "county_code", "tract_code", "block_code"),
    )
