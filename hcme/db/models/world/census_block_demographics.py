import sqlalchemy as sa
from sqlalchemy.sql.schema import CheckConstraint, UniqueConstraint

from hcme.db.abstract import Base


class CensusBlockAge(Base):
    """Age related demographics at the census blcok level."""

    __tablename__ = "census_block_age"

    block_id = sa.Column(sa.String, sa.ForeignKey("census_block.id"), nullable=False)

    pct = sa.Column(
        sa.Float,
        nullable=False,
    )

    count = sa.Column(
        sa.Integer,
        nullable=False,
    )

    pct_veteran = sa.Column(sa.Float, nullable=False)

    lower_bound = sa.Column(sa.Integer, nullable=False)

    upper_bound = sa.Column(sa.Integer, nullable=False)

    # Should be "M" or "F"
    sex = sa.Column(sa.String(length=1), nullable=False)

    __table_args__ = (
        CheckConstraint(pct.between(0, 1, symmetric=True)),
        CheckConstraint(pct_veteran.between(0, 1, symmetric=True)),
        CheckConstraint(sex.in_(["M", "F"])),
        UniqueConstraint(
            "block_id",
            "sex",
            "lower_bound",
            name="census_block_age_block_id_sex_agerange",
        ),
    )


class CensusBlockHousehold(Base):

    __tablename__ = "census_block_household"

    block_id = sa.Column(sa.String, sa.ForeignKey("census_block.id"), nullable=False)

    pct_family_household = sa.Column(sa.Float, nullable=False)

    pct_nonfamily_household = sa.Column(sa.Float, nullable=False)

    pct_nonfamily_alone = sa.Column(sa.Float, nullable=False)

    __table_args__ = (
        CheckConstraint(pct_family_household.between(0, 1, symmetric=True)),
        CheckConstraint(pct_family_household + pct_nonfamily_household == 1),
        UniqueConstraint("block_id", name="census_block_household_block_id"),
    )


class CensusBlockEconomics(Base):

    __tablename__ = "census_block_economics"

    block_id = sa.Column(sa.String, sa.ForeignKey("census_block.id"), nullable=False)

    pct = sa.Column(sa.Float, nullable=False)

    household_income_lower_bound = sa.Column(sa.Integer, nullable=False)

    household_income_upper_bound = sa.Column(sa.Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "block_id",
            "household_income_lower_bound",
            "household_income_upper_bound",
            name="census_block_econ_block_id_bounds",
        ),
    )
