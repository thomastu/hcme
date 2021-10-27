import sqlalchemy as sa

from hcme.db import Base


class Fleet(Base):

    __tablename__ = "fleets"

    # Foreign key to SupplyScenario
    scenario_id = sa.Column(
        sa.Integer, sa.ForeignKey("supply_scenarios.id"), primary_key=True
    )

    # Relationships
    scenario = sa.orm.relationship("SupplyScenario", back_populates="fleets")

    # Fleet size
    size = sa.Column(sa.Integer)

    # Capacity per vehicle
    capacity = sa.Column(sa.Integer)

    # miles per gallon
    mpg = sa.Column(sa.Float)
