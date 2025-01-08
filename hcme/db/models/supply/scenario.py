import sqlalchemy as sa
from sqlalchemy.orm import relationship

from hcme.db import Base


class SupplyScenario(Base):

    __tablename__ = "supply_scenarios"

    name = sa.Column(sa.String(length=100), unique=True, index=True, nullable=False)

    description = sa.Column(sa.Text, nullable=True)

    experiments = relationship("Experiment", back_populates="supply_scenario")

    fleets = relationship("Fleet", back_populates="scenario")
